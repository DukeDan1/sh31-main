'''View renderers for Django.'''

from http import HTTPStatus
import json
import os
import threading
import django
from django.conf import settings
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from analyzer.forms import DocumentUploadForm, UserProfileForm
from analyzer.io.common import PendingRecord, generic_openai_request, write_unhandled_error
from analyzer.io.messages import get_messages_by_uuid, get_owned_documents, NIL_UUID
from analyzer.io.nlp import (get_messages_nlp_progress, get_profile_from_topic,
                             run_nlp_on_messages, wait_nlp_tasks)
from analyzer.io.relation import set_profile_relation
from analyzer.models import Document, Message, NLPTask, Profile, RecentActivity, SystemUser
from analyzer.io import views_helper
from data_ingestion import file_handling
from graph import plot

def not_found(request, exception):
    '''Stub for not found page as redirect target.'''
    id(exception)
    response = render(request, 'error.html')
    response.status_code = HTTPStatus.NOT_FOUND
    return response

@login_required
def unspecified_profile(request):
    '''Redirect when the profile is unspecified.'''
    requester = SystemUser.objects.get(user=request.user)
    all_profiles = Profile.objects.all()
    if not all_profiles.exists():
        return redirect(f"{reverse('upload')}?error=nodocs")
    last_profile_pks = (RecentActivity.objects.filter(user=requester).exclude(profile=None)
                        .order_by('-activity_time').values_list('profile', flat=True))
    profile_pk = (last_profile_pks.first()
                  if last_profile_pks.exists()
                  else all_profiles.first().pk)
    return redirect('profile', profile_pk)

@login_required
def unspecified_message(request):
    '''Redirect when the message is unspecified.'''
    requester = SystemUser.objects.get(user=request.user)
    first_document = get_owned_documents(request.user).first()
    if first_document is None:
        return redirect(f"{reverse('upload')}?error=nodocs")
    last_document_uuids = (RecentActivity.objects
        .filter(user=requester).exclude(document=None)
        .order_by('-activity_time').values_list('document', flat=True))
    document_uuid = (last_document_uuids.first()
                        if last_document_uuids.exists()
                        else first_document.uuid)
    return redirect('messages_view', document_uuid)

@login_required
def profile(request, profile_id):
    '''Returns a rendered base template as a placeholder.'''
    requester = SystemUser.objects.get(user=request.user)

    profile_data = get_object_or_404(Profile, pk=profile_id)
    # Fetch documents where the profile has sent a message
    associated_documents = Document.objects.filter(message__owner=profile_data).distinct()
    average_risk = views_helper.get_profile_risk_stat(profile_data)
    profile_risk_graph = plot.profile_risk_gauge(average_risk)

    message_objs = Message.objects.filter(owner=profile_data)
    nlp_results, _ = wait_nlp_tasks(message_objs)
    populated_dict = plot.populate_nlp_dict(nlp_results)

    message_risk_graph = plot.profile_risk_graph(populated_dict)
    set_profile_relation(profile_data)

    if requester.query_tracking_enabled:
        user_activity = (RecentActivity.objects
                         .get_or_create(user=requester, profile=profile_data)[0])
        user_activity.save()

    return render(request, 'profile.html', {
        'profile': profile_data,
        'related_profiles': profile_data.related_profiles.all(),
        'associated_documents': associated_documents,
        'risk_graph': profile_risk_graph,
        'message_risk_graph' : message_risk_graph,
        'average_risk' : average_risk
    })

@login_required
def upload(request):
    '''Returns the rendered file upload page.'''
    return render(request, 'upload.html', context={
        'form': DocumentUploadForm(),
        'show_error': False if not request.GET.get('error', False) else request.GET.get('error')
    })

@login_required
@csrf_protect
def api_upload_file(request):
    '''API endpoint for uploading files'''
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploader = SystemUser.objects.get(user=request.user)
                file_record = form.save(commit=False)
                file_record.display_name = request.FILES['file'].name
                file_record.owner = uploader
                file_record.save()
                processor = file_handling.FileProcessor(file_record.file.path)
                processor.process()
                if processor.is_valid():
                    preview = processor.file.get_data()
                    file_name = processor.file.save(uploader)
                    return JsonResponse({
                    "form": form.as_ul(), "preview": preview, "success":True, "file_name": file_name
                    })
                return JsonResponse({
                    "success": False, "error": "Could not parse this file."
                })
            except file_handling.InvalidFileException:
                return JsonResponse({
                    "success": False,
                    "error": "Could not parse this file. Check that this is a valid file type."
                 })



        print(form.errors)
        return JsonResponse({
            "error": form.errors.as_ul(), "success":False
            })

    return JsonResponse({
        "error": "This endpoint only accepts POST requests.", "success":False
        })

@login_required
@csrf_protect
def api_accept_file(request):
    '''API endpoint for accepting files'''
    if request.method == 'POST':
        return_value = None
        try:
            request_data = json.loads(request.body)
            filename = request_data["file_name"]
            uuid, ext = os.path.splitext(filename.split("/")[-1])
            record = PendingRecord(Document.objects.get(uuid=uuid))
            path_parsed = os.path.join(settings.MEDIA_ROOT, 'ingestion_saves', uuid)
            path_parsed += ext
            parsed_file = views_helper.read_json_from_file(path_parsed)
            fields = views_helper.parse_field_mapping(request_data["field_mapping"])
            views_helper.populate_message(uuid, fields, parsed_file)

            record.accept()

            # Get OpenAI data in the background, it will be saved and display when ready.
            openai_request_thread = threading.Thread(
                target=record.get_openai_data, args=(parsed_file,)
            )
            openai_request_thread.start()

            return_value = JsonResponse({
                "success": True,
                "message": f'''
                    Your file has been accepted.
                    <a href="{reverse('messages_view', args=[uuid])}">See it here</a>
                '''
            })

        except KeyError:
            return_value =  JsonResponse({
                "success": False,
                "error": "No file name was provided."
            })
        except django.db.utils.IntegrityError:
            return_value =  JsonResponse({
                "success": False,
                "error": "A problem has occurred whilst saving this file."
            })
        except Document.DoesNotExist:
            return_value =  JsonResponse({
                "success": False,
                "error": "This file was not found in the database."
            })
        except ValidationError:
            return_value =  JsonResponse({
                "success": False,
                "error": "Your field mapping is not valid. Please check your choices and try again."
            })
        except Exception as e: # pylint: disable=broad-except
            # Something else has gone wrong
            print(e)
            return_value = JsonResponse({
                "success": False,
                "error": """Something went wrong. Please check your field mapping and try again."""
            })
            write_unhandled_error(e, "api_accept_file")

        return return_value

    return JsonResponse({
        "error": "This endpoint only accepts POST requests.", "success":False
    })

@login_required
@csrf_protect
def api_reject_file(request):
    '''API endpoint for rejecting files'''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            filename = data["file_name"]
            uuid, _ext = os.path.splitext(filename.split("/")[-1])

            record = PendingRecord(Document.objects.get(uuid=uuid))
            record.reject()

            return JsonResponse({
                "success": True,
                "message": "Your file has been rejected."
            })
        except KeyError:
            return JsonResponse({
                "success": False,
                "error": "No file name was provided."
            })
        except django.db.utils.IntegrityError:
            return JsonResponse({
                "success": False,
                "error": "This file was not found in the database."
            })
        except ValidationError:
            return JsonResponse({
                "success": False,
                "error": "Invalid file name. Please check your file name and try again."
            })
        except Document.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "This file was not found in the database."
            })

    return JsonResponse({
        "error": "This endpoint only accepts POST requests.", "success":False
    })

@login_required
def api_message(request, message_id):
    '''Returns the rendered message view page.'''
    message_obj = get_object_or_404(Message, pk=message_id)
    run_nlp_on_messages([message_obj])

    requester = SystemUser.objects.get(user=request.user)
    if not request.user.is_superuser and message_obj.source.owner != requester:
        return JsonResponse({
            'error': 'You do not have permission to view this message.',
            'success': False
        })

    results_json = NLPTask.objects.get(message=message_obj).result
    if results_json is None:
        return JsonResponse({'pending': True})
    results = json.loads(results_json)

    # Updated section to include profile links for keywords
    keywords = []
    for topic in results['topics']:
        keyword = {'concept': topic[1], 'keyword': topic[0]}
        if matched_profile := get_profile_from_topic(keyword):
            keyword['profile_id'] = matched_profile.pk
        keywords.append(keyword)

    if results['risk'] > 0.4:
        risk_description = 'LOW'
    elif results['risk'] < -0.4:
        risk_description = 'HIGH'
    else:
        risk_description = 'MEDIUM'

    sentiment = 'very ' if abs(results['sentiment']) > 0.7 else 'slightly '
    sentiment += 'positive' if results['sentiment'] > 0 else 'negative'

    return JsonResponse({
        'pending': False,
        'document_name': message_obj.source.display_name,
        'owner_name': message_obj.owner.name,
        'message_body': message_obj.body,
        'message_date': message_obj.date,
        'message_risk_score': f'{risk_description} ({round(results["risk"], 3)})',
        'message_sentiment': sentiment,
        'message_source': message_obj.source.uuid,
        'concept_analysis_data': keywords,
    })

def login(request):
    '''Returns the login page.'''
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')

def signup(request):
    '''Returns the signup page.'''
    error = None
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.is_active = False
            user.save()
            SystemUser(user=user).save()
            error = 'Access request logged, please wait for approval.'
        else:
            error_strings = []
            for field in form:
                error_strings.extend(field.errors)
            error = error_strings[0]
    else:
        form = UserProfileForm()
    return render(request, 'signup.html', context={'user_form': form, 'error': error})

@login_required
def dashboard(request):
    '''Returns the dashboard page.'''

    has_tasks_pending = False
    selected_uuid = NIL_UUID

    if request.method == 'POST':
        selected_uuid = request.POST.get('selected_document')

    messages_query = get_messages_by_uuid(request.user, selected_uuid)
    graphs_desc_pair = views_helper.graph_logic(request.user, selected_uuid)
    if graphs_desc_pair is None:
        has_tasks_pending = True
        graphs, description = plot.empty_graph_analysis(5)
    else: graphs, description = graphs_desc_pair



    activities = RecentActivity.objects.filter(
    user=views_helper.get_user(request)).order_by('-activity_time')

    document_activity_strings = []

    for activity in activities.exclude(document=None)[:3]:
        formatted_time = activity.activity_time.strftime('%I:%M%p %Z on %b %d, %Y')
        url = reverse("messages_view", args=[str(activity.document.pk)])
        document_activity_strings.append(f'You recently visited <a href="{url}" '
            f'class="text-primary">{activity.document.display_name}</a> at {formatted_time}.')

    owned_documents = get_owned_documents(request.user)
    dropdown_documents = [{
        'uuid': NIL_UUID, 'display_name': 'All Documents'
    }] + list(owned_documents)
    selected_document_name = ('All Documents' if selected_uuid == NIL_UUID
                              else Document.objects.get(uuid=selected_uuid).display_name)

    return render(request, 'dashboard.html', context={
        'recent_document_activities': document_activity_strings,
        'recent_profiles': Profile.objects.filter(pk__in=activities
            .exclude(profile=None)[:3].values_list('profile')),
        'recent_tracking_disabled': not views_helper.get_user(request).query_tracking_enabled,
        'should_refresh': 'true' if has_tasks_pending else 'false',
        'initial_progress': get_messages_nlp_progress(messages_query),
        'documents': dropdown_documents,
        'selected': selected_document_name,
        'chatbot_documents': owned_documents,
        'document_id': owned_documents.first().uuid if owned_documents.exists() else None,
        'chatbot_show_document_list': len(owned_documents) > 1,
        'hide_chatbot': not owned_documents.exists()
    } | {f'graph_{i + 1}': graph[0] for i, graph in enumerate(graphs)}  |
      {f'graph_{i +1}_meaning': meaning for i,meaning in enumerate(description)})

@login_required
def logout(request):
    '''Returns the login page.'''
    django_logout(request)
    return redirect('login')

@login_required
def api_chatbot(request):
    '''Sends a chatbot request to OpenAI'''
    # required data: chat history, file name
    if request.method == 'POST':
        error = "An unknown error occurred."
        try:
            data = json.loads(request.body)
            user_messages = data['user_messages']

            if data.get('mock', False):
                return JsonResponse({
                    'messages': generic_openai_request(
                    views_helper.chatbot_request,
                    [],
                    [],
                    True
                ), 'success': True})

            file_name = Document.objects.get(
                uuid=data['document_id'],
                accepted=True,
                is_ingestion_output=True).file.name
            if not file_name:
                raise FileNotFoundError("The file you are trying to access does not exist.")

            _, ext = os.path.splitext(file_name)
            with open(os.path.join(
                settings.MEDIA_ROOT, 'ingestion_saves', data['document_id'] + ext),
                'r', encoding='utf8'
            ) as f:
                response = generic_openai_request(
                    views_helper.chatbot_request,
                    user_messages,
                    f.read()
                )

                response['content'] = response['content'].replace('```html', '').replace('```', '')

                if response:
                    user_messages.append(response)
                else:
                    return JsonResponse({
                        "error": "Unable to make this request. Please try again.", "success":False
                    })

                return JsonResponse({"messages": user_messages, "success":True})

        except FileNotFoundError:
            error = "The file you are trying to access does not exist."
        except KeyError:
            error = "Required data has not been provided."
        except json.JSONDecodeError:
            error = "The data provided is not valid JSON."
        return JsonResponse({"error": error, "success":False})
    return JsonResponse({
        "error": "This endpoint only accepts POST requests.", "success":False
    })

@login_required
def messages_view(request, document_id):
    '''Returns the rendered document page.'''
    requester = SystemUser.objects.get(user=request.user)
    all_documents = get_owned_documents(request.user)[:30]

    try:
        document = Document.objects.get(pk=document_id)
    except(django.core.exceptions.ObjectDoesNotExist, django.core.exceptions.ValidationError):
        return redirect('unspecified_message')

    if requester.query_tracking_enabled:
        user_activity = RecentActivity.objects.get_or_create(user=requester, document=document)[0]
        user_activity.save()

    document_messages = Message.objects.filter(source=document).order_by('date')

    first_message_owner = document_messages.first().owner

    if not request.user.is_superuser and document.owner != requester:
        return redirect(f"{reverse('upload')}?error=noperms")

    # create risk and sentiment graphs
    openai_data = document.openai_data

    if (openai_data and
        openai_data.get('risk_score_messages') and
        openai_data.get('sentiment_messages')):

        sentiment_risk_graph = plot.get_graph_risk_and_sentiment({
            'ID': [index for index, _ in enumerate(openai_data['risk_score_messages'])],
            'Risk': openai_data['risk_score_messages'],
            'Sentiment': openai_data['sentiment_messages']
        })
    else:
        sentiment_risk_graph = None

    sorted_document_messages_by_risk = None
    if openai_data and openai_data.get('risk_score_messages'):
        sorted_document_messages_by_risk = sorted(
            zip(list(document_messages), openai_data['risk_score_messages']),
            key=lambda x: x[1], reverse=True
        )

    views_helper.delete_pending_documents(request)

    return render(request, 'messages_view.html', context={
        'chatbot_show_document_list': len(all_documents) > 1,
        'documents': all_documents,
        'chatbot_documents': all_documents,
        'hide_chatbot': False,
        'document_name': document.display_name,
        'document_id': document.uuid,
        'messages': document_messages,
        'sorted_messages': [x[0] for x in sorted_document_messages_by_risk]
        if sorted_document_messages_by_risk else document_messages,
        'first_message_owner': first_message_owner,
        'sentiment_risk_graph': sentiment_risk_graph,
        "openai": openai_data,
        'initial_progress': get_messages_nlp_progress(document_messages),
    })

@login_required
def settings_view(request):
    '''Returns the settings page and handles password change.'''
    if request.method == 'POST':
        password_change_form = PasswordChangeForm(user=request.user, data=request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            # Update session to prevent logout
            django_login(request, password_change_form.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('settings')
        messages.error(request, 'Error changing password.')
    else:
        password_change_form = PasswordChangeForm(user=request.user)

    return render(request, 'settings.html', {
        'query_tracking_enabled': SystemUser.objects.get(user=request.user).query_tracking_enabled,
        'password_change_form': password_change_form
    })

@login_required
def profile_search(request):
    '''Search for profiles based on the user input.'''
    search_query = request.GET.get('profile_search', '')

    if search_query:
        profiles = Profile.objects.filter(name__icontains=search_query)
    else:
        profiles = Profile.objects.all()

    return render(request, 'profile_search_results.html', {'profiles': profiles})

@login_required
def api_document_search(request):
    '''API endpoint for searching for documents.'''
    all_documents = get_owned_documents(request.user)
    data = json.loads(request.body)

    try:
        query = data['query']
        show_all = data.get('show_all', False)
    except KeyError:
        return JsonResponse({
            "message": "Your request is missing required fields.", "success":False
        })

    if not show_all:
        return JsonResponse({
            "success": True,
            "result": [
                {
                    "display_name": x.display_name,
                    "url": x.get_url(),
                    "file_name": x.file.path
                }
                for x in
                all_documents.filter(
                    display_name__icontains=query,
                    accepted=True,
                    is_ingestion_output=True
                )
            ]
        })
    return JsonResponse({
        "success": True,
        "result": [
            {
                "display_name": x.display_name,
                "url": x.get_url(),
                "file_name": x.file.path
            }
            for x in
            all_documents.filter(accepted=True, is_ingestion_output=True)
        ]
    })

@csrf_protect
def api_login(request):
    '''API endpoint for logging in.'''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data['username']
            password = data['password']
        except KeyError:
            return JsonResponse({
                "message": "Your request is missing required fields.", "success":False
            })

        try:
            user = authenticate(username=username, password=password)
            response_data = {
                'success':False,
                'message': 'Your email and password do not match, or your account is inactive.'
            }

            if user:
                django_login(request, user)
                response_data['success'] = True
                response_data['message'] = 'Successfully logged in.'

            return JsonResponse(response_data)
        except Exception as e: # pylint: disable=broad-except
            print(e)
            return JsonResponse({"message": "An unknown error occurred.", "success":False})


    else:
        return JsonResponse({
            "message": "This endpoint only accepts POST requests.", "success":False
        })

@login_required
def update_query_tracking(request):
    '''Enable Query Tacking button saved for each user'''
    if request.method == 'POST':
        user_profile = SystemUser.objects.get(user=request.user)
        user_profile.query_tracking_enabled = 'query_tracking' in request.POST
        user_profile.save()
        if not user_profile.query_tracking_enabled:
            RecentActivity.objects.filter(user=user_profile).delete()
        messages.success(request, 'Query tracking preference updated.')
    return redirect('settings')

@login_required
def api_nlp_process(request):
    '''Queues the requested document for NLP processing, and asks for progress.'''
    if request.method != 'POST':
        return JsonResponse({
            'message': 'This endpoint only accepts POST requests.', 'success': False
        })

    data = json.loads(request.body)
    filename = data['file_name']
    if filename is None:
        message_objs = Message.objects.all()
    else:
        uuid, _ext = os.path.splitext(filename.split("/")[-1])
        parent_document = Document.objects.get(uuid=uuid)
        message_objs = Message.objects.filter(source=parent_document)

    if data['initial']:
        run_nlp_on_messages(message_objs)

    return JsonResponse({
        'progress': get_messages_nlp_progress(message_objs), 'success': True
    })

@login_required
def update_profile_note(request, profile_id):
    '''Allows the user to save notes for profiles'''
    profile_obj = get_object_or_404(Profile, pk=profile_id)  # Renamed variable to 'profile_obj'
    if request.method == 'POST':
        profile_obj.note = request.POST.get('freeform')
        profile_obj.save()
        return redirect('profile', profile_id=profile_id)
    return redirect('profile', profile_id=profile_id)

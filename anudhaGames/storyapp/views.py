from django.shortcuts import render,redirect
from .forms import *
from django.http import JsonResponse
import firebase_admin
from firebase_admin import auth,firestore
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .story import *
from firebase_config import db
import json
import random
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt




def index(request):
    img_ref = db.collection('staticimg')  # Get 'staticimg' collection
    docs = img_ref.get()  # Fetch all documents
    images = []
    for doc in docs:
        doc1 = doc.id
        data = doc.to_dict()
        about = data.get('about', '')
        admission = data.get('admission', '')
        bg = data.get('bg', '')
        body_bg = data.get('body_bg', '')
        determine = data.get('determine', '')
        hero = data.get('hero', '')
        hero_bg = data.get('hero_bg', '')
        hero_bg_old = data.get('hero_bg_old', '')
        hero_bg2 = data.get('hero_bg2', '')
        hero_bg2_old = data.get('hero_bg2_old', '')
        logo = data.get('logo', '')
        students = data.get('students', '')
        why = data.get('why', '')
        images.append({'about': about, 'admission': admission, 'bg': bg, 'body_bg': body_bg, 'determine': determine, 'hero': hero, 'hero_bg': hero_bg, 'hero_bg_old': hero_bg_old, 'hero_bg2': hero_bg2, 'hero_bg2_old': hero_bg2_old, 'logo': logo, 'students': students, 'why': why})
    return render(request, 'index.html', {"images": images})

def forget(request):
    return render(request, 'forget.html')

def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Create user in Firebase Auth
            user = auth.create_user(email=email, password=password)
            user_id  = user.uid  # Get the unique Firebase user ID
            
            # Store user data in Firestore
            user_ref = db.collection("User").document(user_id)
            user_ref.set({
                "username": "user",  # Default username
                "email": email,
                "userpoints": 0  # Default points
            })

            messages.success(request, "Registration successful. Please log in.")
            return redirect("index")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("index")

    return render(request, "index.html")


@csrf_exempt  # Disable CSRF just for this token endpoint (since it's called via JS)
def verify_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_token = data.get("token")

            #  Verify Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            email = decoded_token["email"]

            #  Get user data from Firestore
            user_doc = db.collection("User").document(uid).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}

            #  Set session
            request.session["user_id"] = uid
            request.session["email"] = email
            request.session["username"] = user_data.get("username", "user")
            request.session["userpoints"] = user_data.get("userpoints", 0)

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=405)


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract form data
            uname = form.cleaned_data['uname']
            uemail = form.cleaned_data['uemail']
            phone_number = form.cleaned_data['phone_number']
            message = form.cleaned_data['message']

            # Prepare data for Firestore
            contact_data = {
                "uname": uname,
                "uemail": uemail,
                "phone_number": phone_number,
                "message": message
            }

            # Store data in Firestore (inside 'contacts' collection)
            db.collection('contacts').add(contact_data)

            messages.success(request, "Your message has been submitted successfully!")
            return redirect("index")  # Redirect to contact page after submission

    else:
        form = ContactForm()

    return render(request, "index.html", {"form": form})


# Logout View (Clears the session)

def logout(request):
    request.session.flush()  # Clear session
    messages = [
        "Goodbye, little hero! The story world will miss you. See you soon! 🌟",
        "Logging out... Your adventure is saved and your friends are waving goodbye! 👋✨",
        "Thanks for playing! Rest up, adventurer — new stories await tomorrow! 🛏📖",
        "You're leaving the storybook, but the magic will be here when you return! ✨🦄",
        "Bye-bye! Your fairy pals say, 'Come back soon!' 🧚‍♀💫",
        "Psst... even heroes need snack breaks. Come back after your cookie! 🍪🦸",
        "Zzz... the story is sleeping now. It'll be ready for you next time! 😴📚"
    ]
    selected_msg = random.choice(messages)
    return render(request, 'logout.html', {'logout_message': selected_msg})


def storylist(request):
    user_email = request.session.get("email")
    stories_ref = db.collection('stories')  # Get 'stories' collection
    docs = stories_ref.get()  # Fetch all documents
    stories = []
    for doc in docs:
        story_id = doc.id
        data = doc.to_dict()
        nodes = data.get('nodes', {})
        # first_node_id = next(iter(nodes), None)  # Get the first node key
        first_node_id = 1  # Get the first node key
        # print(f"** {first_node_id}")
        story_name = data.get('story_name', 'Unknown Story')
        image = data['nodes'].get('1', {}).get('image_url', '')
        r_points = data.get('required_points',0)
        

        # print(f"Story: {story_name}, Image URL: {image}")  # Debugging output

        stories.append({'id': story_id, 'story_name': story_name, 'image': image, 'node_id': first_node_id, 'required_points': r_points})

    # Images url
    img_ref = db.collection('staticimg')  # Get 'staticimg' collection
    imgdocs = img_ref.get()  # Fetch all documents
    images = []
    for doc in imgdocs:
        doc1 = doc.id
        data = doc.to_dict()
        logo = data.get('logo', '')
        images.append({'logo': logo})

    if user_email:
        user_email = request.session.get("email")
        username = request.session.get("username", "user")
        userpoints = request.session.get("userpoints", 0)
        user_id = request.session["user_id"]

        user_total_points = get_user_total_points(user_id)

        return render(request, "storylist.html", {"stories": stories, "images":images, "email": user_email, "username": username, "userpoints": userpoints, "user_total_points": user_total_points})
    else:
        # messages.error(request, "Please log in first.")
        return redirect("index")  


def story(request, story_id, node_id="1"):
    # for key, value in request.session.items():
    #     print(f"{key}: {value}")

    user_id = request.session["user_id"]
    user_email = request.session.get("email")
    username = request.session.get("username", "user")

    # Images url
    img_ref = db.collection('staticimg')  # Get 'staticimg' collection
    imgdocs = img_ref.get()  # Fetch all documents
    images = []
    for doc in imgdocs:
        doc1 = doc.id
        data = doc.to_dict()
        logo = data.get('logo', '')
        reward = data.get('reward', '')
        totalreward = data.get('totalreward', '')
        qbg2 = data.get('qbg2', '')
        images.append({'reward': reward, 'totalreward': totalreward, 'qbg2': qbg2,'logo': logo})

    if not user_id:
        messages.error(request, "Please log in first.")
        return redirect("index")
    # print(f"** Byeeee1")
    
    story_ref = db.collection("stories").document(story_id)
    story_doc = story_ref.get()
    if not story_doc.exists:
        messages.error(request, "Story not found.")
        # print(f"** Byeeee2")
        return redirect("storylist")

    story_content = story_doc.to_dict()
    nodes = story_content.get("nodes", {})

    if node_id not in nodes:
        # messages.error(request, "Invalid story node.")
        # print(f"** Byeeee3")
        # print(node_id)
        return redirect("storylist")

    # print(f"** Byeeee4")

    current_node = nodes[node_id]
    question = current_node.get("question", "")
    image = current_node.get("image_url", "")
    choices = current_node.get("choices", {})
    next_node = current_node.get("next", None)
    e_points = current_node.get("points", 0)

    user_story_ref = db.collection("User").document(user_id).collection("stories").document(story_id)
    user_story_doc = user_story_ref.get()
    user_story_content = user_story_doc.to_dict() if user_story_doc.exists else {}
    
    choices_rewarded = user_story_content.get("choices_rewarded", [])

    #### 🛠 Find choice_id based on which choice led here ####
    choice_id = None
    for parent_node_id, parent_node in nodes.items():
        for choice_key, child_node_id in parent_node.get("choices", {}).items():
            if child_node_id == node_id:
                choice_id = child_node_id  # Important: child_node_id == this node_id
                break
        if choice_id:
            break

    #### 🛠 Reward points only if not already rewarded ####
    if choice_id:
        if choice_id in choices_rewarded:
            messages.info(request, "You've already earned points for this choice! Let's Explore Other Choices")
        else:
            earned_points = current_node.get("points", 0)

            choices_rewarded.append(choice_id)
            user_story_ref.set({
                "points": user_story_content.get("points", 0) + earned_points,
                "choices_rewarded": choices_rewarded,
            }, merge=True)

            if earned_points:
                update_user_points(user_id, story_id, earned_points)

    user_total_points = get_user_total_points(user_id)
    user_story_points = get_user_story_points(user_id, story_id)
    current_points = get_user_current_points(story_id, node_id)

    context = {
        "story_id": story_id,
        "story_name": story_content.get("story_name", ""),
        "image": image,
        "question": question,
        "choices": choices,
        "node_id": next_node,
        "user_session_points": int(user_story_points or 0),
        "user_total_points": int(user_total_points or 0),
        "current_points": current_points,
        "email": user_email,
        "username": username,
        "e_points":int(e_points or 0),
        "images": images,
    }
    return render(request, "story.html", context)

# @login_required
def profile(request):
    user_id = request.session.get("user_id")  # Get logged-in user ID
    user_ref = db.collection("User").document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
    else:
        user_data = {}

    if request.method == "POST":
        new_username = request.POST.get("username")
        new_email = request.POST.get("email")

        try:
            # Update Firestore username
            user_ref.update({"username": new_username})

            # Update Firebase Auth email
            auth.update_user(user_id, email=new_email)

            # Update Firestore email
            user_ref.update({"email": new_email})

            messages.success(request, "Profile updated successfully!")
            return redirect("index")

        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")

    return render(request, "profile.html", {"user": user_data})


def story_selection(request):
    user_id = request.session.get("user_id", "default_user")
    user_points = get_user_total_points(user_id)
    stories = get_all_stories(user_points)
    
    return render(request, "storylist.html", {"stories": stories, "user_points": user_points})


def handle_choice(request, story_id, node_id):
    chosen_option = request.GET.get("choice")
    story_node, _ = get_story_node(story_id, node_id)

    if not story_node or "choices" not in story_node:
        return render(request, "error.html", {"message": "Invalid choice."})

    next_node = story_node["choices"].get(chosen_option, "1")
    return redirect("story", story_id=story_id, node_id=next_node)



def check_story_status(request, story_id,node_id):
    user_id = request.session.get('user_id')  # Assuming you're storing user_id in session
    if not user_id:
        return JsonResponse({'error': 'Not logged in'}, status=403)
    
    # print(f"** Helloooo1")
    user_story_ref = db.collection('User').document(user_id).collection('stories').document(story_id)
    story_ref = db.collection('stories').document(story_id)
    user_story_doc = user_story_ref.get()
    story_doc = story_ref.get()
    # print(f"** Helloooo2")
    if not user_story_doc.exists or not story_doc.exists:
        # print(f"** Helloooo3")
        return JsonResponse({'error': 'Story not found'}, status=404)
    # print(f"** Helloooo4")
    user_story_data = user_story_doc.to_dict()
    story_data = story_doc.to_dict()
    choices_rewarded = user_story_data.get('choices_rewarded', [])
    # print(f"Rewarded choices: {choices_rewarded}")

    # Now extract all choices from all nodes in the story
    all_choices = set()
    nodes = story_data.get('nodes', {})
    for node_id, node_data in nodes.items():
        choices = node_data.get('choices', {})
        all_choices.update(choices.values())  # Add choice node IDs

    # print(f"All possible choices from story: {all_choices}")

    all_explored = set(choices_rewarded) == all_choices
    # print(f"All explored? {all_explored}")

    story_points = user_story_data.get('points', 0)

    return JsonResponse({
        'all_explored': all_explored,
        'story_points': story_points
    })




def reset_story_points(request, story_id,node_id):
    # print(f"** RESET----")
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not logged in'}, status=403)

    user_ref = db.collection('User').document(user_id)
    user_story_ref = user_ref.collection('stories').document(story_id)

    user_story_doc = user_story_ref.get()
    user_doc = user_ref.get()

    if not user_story_doc.exists or not user_doc.exists:
        return JsonResponse({'error': 'Documents not found'}, status=404)

    story_points = user_story_doc.to_dict().get('points', 0)
    total_points = user_doc.to_dict().get('userpoints', 0)

    # Subtract story points from total
    updated_total = total_points - story_points

    # Update Firestore
    user_ref.update({'userpoints': updated_total})
    user_story_ref.update({'points': 0, 'choices_rewarded': []})

    return JsonResponse({'success': True})

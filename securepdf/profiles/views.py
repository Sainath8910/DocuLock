from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
import random
import base64, hashlib

from core.models import Question

User = get_user_model()


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("select_action")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def dashboard_view(request):
    return render(request, "users/dashboard.html")


def generate_key(answer: str):
    """Generate a Fernet-compatible key from an answer string."""
    digest = hashlib.sha256(answer.encode()).digest()
    return base64.urlsafe_b64encode(digest)


@login_required
def select_action_view(request):
    """Page to select Encrypt or Decrypt."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "encrypt":
            return redirect("select_receiver")
        elif action == "decrypt":
            return redirect("decrypt_document")
    return render(request, "users/select_action.html")


@login_required
def select_receiver_view(request):
    """Page to select which user to send encrypted doc to."""
    users = User.objects.exclude(id=request.user.id)
    if request.method == "POST":
        receiver_id = request.POST.get("receiver")
        return redirect("upload_document", receiver_id=receiver_id)
    return render(request, "users/select_receiver.html", {"users": users})


def generate_answer_from_pattern(user, pattern: str):
    """
    Generate the answer dynamically from the pattern.
    Example patterns:
        - "DOB:DDMMYYYY"  -> user.dob formatted as DDMMYYYY
        - "USERNAME"      -> user.username
        - "EMAIL"         -> user.email
        - "SCHOOL"        -> user.school
    """
    answer = pattern

    if "DOB" in pattern:
        answer = user.dob.strftime("%d%m%Y")
    if "USERNAME" in pattern:
        answer = user.username
    if "EMAIL" in pattern:
        answer = user.email
    if "SCHOOL" in pattern:
        answer = user.school

    return answer


@login_required
def upload_document_view(request, receiver_id=None):
    """Upload and encrypt document for a selected receiver."""
    if receiver_id:
        receiver = User.objects.get(id=receiver_id)
    else:
        users = User.objects.exclude(id=request.user.id)
        return render(request, "users/upload_document.html", {"users": users})

    if request.method == "POST" and request.FILES.get("document"):
        uploaded_file = request.FILES["document"]
        file_data = uploaded_file.read()

        # Pick a random question
        question_obj = random.choice(Question.objects.all())
        question_text = question_obj.description
        pattern = question_obj.pattern

        # Generate receiver answer dynamically
        receiver_answer = generate_answer_from_pattern(receiver, pattern)

        # Encrypt using receiver's answer
        key = generate_key(receiver_answer)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(file_data)

        # Combine question + pattern + encrypted data
        combined_content = (
            f"QUESTION:{question_text}\nPATTERN:{pattern}\n\n".encode() + encrypted_data
        )

        response = HttpResponse(
            combined_content, content_type="application/octet-stream"
        )
        response["Content-Disposition"] = f'attachment; filename="{uploaded_file.name}.enc"'
        return response

    return render(request, "users/upload_document.html", {"receiver": receiver})


@login_required
def decrypt_document_view(request):
    if request.method == "POST":
        print("*1")
        # Check if a new file is uploaded
        if request.FILES.get("document"):
            print("*1")
            uploaded_file = request.FILES["document"].read()
            
            # Split QUESTION and encrypted data
            try:
                parts = uploaded_file.split(b"\n\n", 1)
                question_line = parts[0].decode()
                encrypted_data = parts[1]
                question = question_line.replace("QUESTION:", "")
            except Exception:
                return HttpResponse("Invalid encrypted file format.", status=400)
            # Render form to ask for answer
            return render(request, "users/decrypt_document.html", {
                "question": question,
                "encrypted_data": encrypted_data  # pass for decryption
            })
        
        # If answer is submitted
        elif "answer" in request.POST and request.POST.get("encrypted_data"):
            answer = request.POST["answer"]
            encrypted_data = request.POST["encrypted_data"].encode('latin1')  # preserve bytes
            
            try:
                key = generate_key(answer)
                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(encrypted_data)
                
                response = HttpResponse(decrypted_data, content_type="application/octet-stream")
                response["Content-Disposition"] = 'attachment; filename="decrypted_file.pdf"'
                return response
            except Exception:
                return HttpResponse("❌ Wrong answer, decryption failed.", status=400)

    # Initial GET → show upload form
    return render(request, "users/decrypt_document.html")

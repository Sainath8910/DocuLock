from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
import random
import base64, hashlib
from django.contrib import messages
import re
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


@login_required
def dashboard_view(request):
    # Get the currently logged-in user
    user = request.user

    context = {
        "user_profile": user
    }
    return render(request, "users/dashboard.html", context)


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


def generate_answer_from_pattern(user, pattern: str) -> str:
    """
    Generate answer from a pattern like:
    'username[:2]+school[:2]+aadhar[-4:]'
    """
    answer = ""
    
    # Split by '+' to handle each field slice
    parts = pattern.split("+")
    
    for part in parts:
        # Match "field[slice]" pattern
        m = re.match(r"(\w+)\[(.*?)\]", part)
        if not m:
            continue
        
        field_name, slice_expr = m.groups()
        value = getattr(user, field_name, "")
        
        # Build slice object safely
        try:
            # slice_expr can be "", ":", "start:end", "-n:", ":-n", etc.
            s = slice(*[int(x) if x else None for x in slice_expr.split(":")])
            answer += value[s]
        except Exception:
            answer += ""  # fallback if slice fails
    print(pattern,answer)
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
        question_title = question_obj.title
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
        f"QUESTION:{question_title}\n"
        f"EXPLANATION:{question_text}\n"
        f"PATTERN:{pattern}\n"
        f"RECEIVER_ID:{receiver.id}\n"
        f"FILENAME:{uploaded_file.name}\n\n".encode()  # <-- use ID here
        + encrypted_data
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
        # Step 1 → File uploaded
        if request.FILES.get("document"):
            uploaded_file = request.FILES["document"].read()

            try:
                # Split headers and encrypted data
                parts = uploaded_file.split(b"\n\n", 1)
                header_lines = parts[0].decode().split("\n")
                encrypted_data = parts[1]

                # Extract question, pattern, and receiver
                question_line = [l for l in header_lines if l.startswith("QUESTION:")][0]
                example = [l for l in header_lines if l.startswith("EXPLANATION:")][0]
                pattern_line = [l for l in header_lines if l.startswith("PATTERN:")][0]
                receiver_line = [l for l in header_lines if l.startswith("RECEIVER_ID:")][0]
                filename_line = [l for l in header_lines if l.startswith("FILENAME:")][0]

                original_filename = filename_line.replace("FILENAME:", "").strip()
                question = question_line.replace("QUESTION:", "").strip()
                pattern = pattern_line.replace("PATTERN:", "").strip()
                intended_receiver_id = int(receiver_line.replace("RECEIVER_ID:", "").strip())

                # 🚨 Check if current user is the intended receiver
                if request.user.id != intended_receiver_id:
                    messages.error(request, "❌ You are not the intended receiver of this file.")
                    return redirect(request.META.get('HTTP_REFERER', '/'))

                # Encode encrypted data safely for HTML
                encrypted_data_b64 = base64.b64encode(encrypted_data).decode("utf-8")

            except Exception as e:
                messages.error(request, f"Invalid encrypted file format. {e}")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            return render(
                request,
                "users/decrypt_document.html",
                {
                    "question": question,
                    "example":example,
                    "pattern": pattern,
                    "encrypted_data": encrypted_data_b64,
                    "original_filename": original_filename,
                },
            )

        # Step 2 → Answer submitted
        elif "answer" in request.POST and request.POST.get("encrypted_data"):
            entered_answer = request.POST.get("answer").strip()
            encrypted_data_b64 = request.POST["encrypted_data"]
            pattern = request.POST.get("pattern")
            original_filename = request.POST.get("original_filename")

            try:
                expected_answer = generate_answer_from_pattern(request.user, pattern)
                if entered_answer != expected_answer:
                    messages.error(request, "❌ Wrong answer, decryption failed.")
                    return redirect(request.META.get('HTTP_REFERER', '/'))

                encrypted_data = base64.b64decode(encrypted_data_b64)
                key = generate_key(entered_answer)
                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(encrypted_data)

                response = HttpResponse(
                    decrypted_data, content_type="application/octet-stream"
                )
                response["Content-Disposition"] = f'attachment; filename="{original_filename}"'
                return response

            except Exception as e:
                messages.error(request, f"❌ Decryption failed. {e}")
                return redirect(request.META.get('HTTP_REFERER', '/'))

    # Initial page load
    return render(request, "users/decrypt_document.html")
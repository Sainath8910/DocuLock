import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import DocumentUploadForm
from .models import Document,Question
from .utils import encrypt_file, decrypt_file
def random_question(request):
    count = Question.objects.count()
    if count == 0:
        return render(request, "core/no_question.html")  # Handle empty DB

    random_index = random.randint(0, count - 1)
    question = Question.objects.all()[random_index]
    return render(request, "core/question.html", {"question": question})


def upload_document(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.sender = request.user

            # ✅ get receiver’s answer (from registration data)
            receiver_answer = doc.receiver.profile.security_answer  

            # ✅ encrypt before saving
            file_data = request.FILES["encrypted_file"].read()
            encrypted_data = encrypt_file(file_data, receiver_answer)

            # overwrite uploaded file with encrypted content
            doc.encrypted_file.file.write(encrypted_data)
            doc.save()

            return redirect("doc_list")
    else:
        form = DocumentUploadForm()
    return render(request, "upload_document.html", {"form": form})


def download_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, receiver=request.user)

    receiver_answer = request.user.profile.security_answer  # ✅ receiver’s own answer
    encrypted_data = doc.encrypted_file.read()
    decrypted_data = decrypt_file(encrypted_data, receiver_answer)

    response = HttpResponse(decrypted_data, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="decrypted_{doc.id}.bin"'
    return response

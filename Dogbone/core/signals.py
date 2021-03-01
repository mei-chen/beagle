import django.dispatch

# before_owner = The django.contrib.auth.models.User before change
# after_owner = The django.contrib.auth.models.User after change
# document = The core.models.Document
document_owner_changed = django.dispatch.Signal(providing_args=["before_owner", "after_owner", "document"])

# sentence = The core.models.Sentence instance
# author = django.contrib.auth.models.User instace
# comment = The actual comment text
comment_posted = django.dispatch.Signal(providing_args=["sentence", "author", "comment"])

# sentence = The core.models.Sentence instance
# user = django.contrib.auth.models.User instace
sentence_liked = django.dispatch.Signal(providing_args=["sentence", "user"])
sentence_unliked = django.dispatch.Signal(providing_args=["sentence", "user"])
sentence_disliked = django.dispatch.Signal(providing_args=["sentence", "user"])
sentence_undisliked = django.dispatch.Signal(providing_args=["sentence", "user"])

# sentence = The core.models.Sentence instance
# author = django.contrib.auth.models.User instace
sentence_edited = django.dispatch.Signal(providing_args=["sentence", "author"])

# sentence = The core.models.Sentence instance
sentence_accepted = django.dispatch.Signal(providing_args=["sentence"])
sentence_rejected = django.dispatch.Signal(providing_args=["sentence"])

sentence_undone = django.dispatch.Signal(providing_args=["sentence"])

# When a ExternalInvite is transformed to a CollaborationInvite
external_invite_transformed = django.dispatch.Signal(providing_args=["external_invite", "collaboration_invite"])

# When collaboration invite is about to be deleted and need to pass in the request.user
collaboration_invite_pre_delete = django.dispatch.Signal(providing_args=["request_user", "instance"])

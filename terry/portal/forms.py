from django import forms


class RewriteNameForm(forms.Form):
    initial_name = forms.CharField(label='Initial name', max_length=100)
    rewritten_name = forms.CharField(label='Rewritten name', max_length=100)


class TreatAsNameForm(forms.Form):
    initial_name = forms.CharField(label='Initial name', max_length=100)
    treat_as_name = forms.CharField(label='Treat As name', max_length=100)

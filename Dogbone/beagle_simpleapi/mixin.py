import json


class SaveModelMixin:
    def save_model(self, model, data, request, *args, **kwargs):
        for field in data:
            setattr(model, field, self.model_data[field])

        model.save()
        return model


class PutDetailModelMixin(SaveModelMixin):
    """
    Add this mixin to a DetailView to add Model update capabilities via PUT
    """

    def validate_put(self, item, request, *args, **kwargs):
        """
        Validate here GET, POST params and `self.model_data`
        :return: True/False
        """
        return True

    def put(self, request, *args, **kwargs):
        self.model_data = json.loads(request.body)
        self.validate_put(self.model_data, request, *args, **kwargs)
        instance = self.get_object(request, *args, **kwargs)
        instance = self.save_model(instance, self.model_data, request, *args, **kwargs)

        serialized = self.to_dict(instance)
        url = self.get_url(instance)
        if url:
            serialized['url'] = url

        return serialized


class DeleteDetailModelMixin:
    """
    Add this mixin to a DetailView to add Model delete capabilities via DELETE
    """

    def validate_delete(self, request, *args, **kwargs):
        """
        Validate here GET, POST params and `self.model_data`
        :return: True/False
        """
        return True

    def delete_model(self, model, request, *args, **kwargs):
        model.delete()
        return model

    def delete(self, request, *args, **kwargs):
        self.validate_delete(request, *args, **kwargs)
        instance = self.get_object(request, *args, **kwargs)

        instance = self.delete_model(instance, request, *args, **kwargs)
        serialized = self.to_dict(instance)

        url = self.get_url(instance)

        if url:
            serialized['url'] = url

        return serialized


class PostListModelMixin(SaveModelMixin):
    """
    Add this mixin to a ListView to add Model creation capabilities via POST
    """
    model = None

    def validate_post(self, item, request, *args, **kwargs):
        """
        Validate here GET, POST params and `self.model_data`

        Raise appropriate exception in case constraints are not satisfied
        """
        return True

    def post(self, request, *args, **kwargs):
        self.model_data = json.loads(request.body)
        if isinstance(self.model_data, dict):
            self.model_data = [self.model_data]

        self.instances = []
        for item in self.model_data:
            self.validate_post(item, request, *args, **kwargs)
            model = self.model()
            instance = self.save_model(model, item, request, *args, **kwargs)
            if instance:
                self.instances.append(instance)

        serialized_instances = []
        for instance in self.instances:
            serialized = self.to_dict(instance)
            url = self.get_url(instance)
            if url:
                serialized['url'] = url
            serialized_instances.append(serialized)

        return serialized_instances

import logging
import math

from django.core.urlresolvers import reverse

from .base import EndpointView, ModelView


class DetailView(ModelView):
    """
    Useful for exposing a single object
    Example url_pattern: '/user/(?P<user_id>[0-9]+)'
    """

    # The name of the model primary key
    model_key_name = 'pk'

    # The name of the primary key in the URL pattern
    url_key_name = 'id'

    # The instance that will be exposed
    instance = None

    @classmethod
    def key_getter(cls, request, *args, **kwargs):
        """
        Get the value of the key from the URL
        """
        return kwargs[cls.url_key_name]

    def get_object(self, request, *args, **kwargs):
        return self.model.objects.get(**{self.model_key_name: self.key_getter(request, *args, **kwargs)})

    def check_model(self):
        if self.model is None:
            raise self.ModelAttachmentException("%s has no attached model" % self.__class__.__name__)

    def upon_successful_get(self, request, *args, **kwargs):
        """ Override this to do stuff after successful view get. """
        pass

    def get(self, request, *args, **kwargs):
        """
        the `GET` method. Get the single detailed object
        """
        try:
            self.check_model()
            self.instance = self.get_object(request, *args, **kwargs)

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            serialized = self.to_dict(self.instance)
            url = self.get_url(self.instance)
            if url:
                serialized['url'] = url

            self.upon_successful_get(self, request, *args, **kwargs)

            return serialized
        except self.model.DoesNotExist as e:
            # The other types of exceptions should be handled
            # by the most generic handler in the parent class
            message = 'Error occurred in DetailView (model.DoesNotExist): %s' % str(e)
            logging.error(message)
            return self.build_error_response(str(e), None, 404)


class ListView(ModelView):
    """
    Useful for exposing a list of object
    Example url_pattern: '/user'
    """

    DEFAULT_RESULTS_PER_PAGE = 20

    object_list = None

    def get_page(self):
        page = self.request.GET.get('page', 0)
        try:
            page = int(page)
        except ValueError:
            page = 0

        return page

    def get_rpp(self):
        """
        Get the results per page
        """
        rpp = self.request.GET.get('rpp', self.DEFAULT_RESULTS_PER_PAGE)
        try:
            rpp = int(rpp)
        except ValueError:
            rpp = self.DEFAULT_RESULTS_PER_PAGE

        return rpp

    def get_page_count(self):
        """
        Override this to get the page count. This can usually get cached.
        It defaults to None since we don't always need the page count, thus
        we want to avoid making an extra query
        """
        return None

    def get_object_count(self):
        """
        Override this to get the object count.
        """
        return None

    def get_queryset(self, request):
        return self.model.objects.all()

    def get_list(self, request, *args, **kwargs):
        return self.get_queryset(request)[self.get_slice()]

    def get_slice(self):
        page = self.get_page()
        rpp = self.get_rpp()
        return slice(page * rpp, (page + 1) * rpp)

    def wrap_result(self, result):
        return {'objects': result}

    def meta(self):
        """
        Provide extra meta data for the API endpoint
        Here we can include stuff like:
        - Pagination
        - Last updated
        - API version
        - Query duration

        It defaults to empty dict so that we can avoid making extra queries
        for endpoints in which we don't need this metadata
        """
        return {}

    def _build_page_url(self, base_url, page, rpp):
        """
        Helper method for building paginated urls
        """
        return "%s?page=%s&rpp=%s" % (base_url, page, rpp)

    def _compute_page_count(self, object_count, rpp):
        """
        Simple formula for computing the page count
        """
        return int(math.ceil(object_count / float(rpp)))

    def pagination(self):
        base_url = reverse(self.endpoint_name)
        page = self.get_page()
        rpp = self.get_rpp()
        page_count = self.get_page_count()
        object_count = self.get_object_count()

        return {
            'page': page,
            'rpp': rpp,
            'page_count': page_count,
            'object_count': object_count,
            'page_url': self._build_page_url(base_url, page, rpp),
            'prev_page': None if page == 0 else page - 1,
            'next_page': None if page_count is None or page >= page_count - 1 else page + 1,
            'prev_page_url': None if page == 0 else self._build_page_url(base_url, page - 1, rpp),
            'next_page_url': None if page_count is None or page >= page_count - 1
                                  else self._build_page_url(base_url, page + 1, rpp),
            'base_url': base_url,
        }

    def get(self, request, *args, **kwargs):
        """
        the `GET` method. Get the single detailed object
        """
        # try:
        if self.model is None:
            raise self.ModelAttachmentException("%s has no attached model" % self.__class__.__name__)

        self.object_list = self.get_list(request, *args, **kwargs)

        filtered_object_list = filter(self.has_access, self.object_list)

        serialized_list = map(self.to_dict, filtered_object_list)

        # Add the URL
        for idx, item in enumerate(serialized_list):
            _url = self.get_url(filtered_object_list[idx])
            if _url:
                item['url'] = _url

        return serialized_list


class ActionView(DetailView):
    """
    Class used for triggering an action
    Example of url_pattern /user/123/promote, /document/1234/promote etc ...
    """

    def action(self, request, *args, **kwargs):
        """ Return True or False """
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        raise self.UnauthorizedException("GET not allowed, use POST")

    def post(self, request, *args, **kwargs):
        """
        the `POST` method. Trigger the actual action
        """
        try:
            if self.model is None:
                raise self.ModelAttachmentException("%s has no attached model" % self.__class__.__name__)

            self.instance = self.get_object(request, *args, **kwargs)

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            # Call the actual action
            result = self.action(request, *args, **kwargs)
            return result
        except self.model.DoesNotExist as e:
            return self.build_error_response(str(e), None, 404)
        except Exception as e:
            return self.build_error_response_from_exception(e)


class ComputeView(EndpointView):
    """
    Useful for POSTing some data and doing some computation on it
    """

    def has_access(self):
        """
        Check that the current user is authorized to use this endpoint
        """
        return True

    def compute(self, request, *args, **kwargs):
        """ Return True or False """
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        logging.error("Reached GET endpoint, class=%s" % str(self.__class__))
        raise self.UnauthorizedException("GET not allowed, use POST")

    def post(self, request, *args, **kwargs):
        """
        the `POST` method. Do the actual computation
        """
        try:

            if not self.has_access():
                raise self.UnauthorizedException("You don't have access to this resource")

            # Call the actual action
            result = self.compute(request, *args, **kwargs)
            return result
        except Exception as e:
            return self.build_error_response_from_exception(e)


class StatusView(EndpointView):
    """
    Useful for GETting some data and doing some computation on it
    """

    def has_access(self):
        """
        Check that the current user is authorized to use this endpoint
        """
        return True

    def status(self, request, *args, **kwargs):
        """ Return True or False """
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        try:
            if not self.has_access():
                raise self.UnauthorizedException("You don't have access to this resource")

            # Call the actual action
            result = self.status(request, *args, **kwargs)
            return result
        except Exception as e:
            return self.build_error_response_from_exception(e)

    def post(self, request, *args, **kwargs):
        raise self.UnauthorizedException("POST not allowed, use GET")

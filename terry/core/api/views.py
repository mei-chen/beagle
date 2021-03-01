from rest_framework.response import Response
from rest_framework.views import APIView

from terry.utils import check_if_repo_exists, clean_repo_url


class RepoDetails(APIView):

    def post(self, request):
        try:
            repo_url = request.data['git_url'].strip()
            if not repo_url.startswith('http'):
                repo_url = 'https://' + repo_url

            repo_url, _ = clean_repo_url(repo_url)

            response = {
                'repo_url': repo_url,
                'exists': check_if_repo_exists(repo_url)
            }
        except Exception as e:
            response = {'exception': '%s: %s' % (e.__class__.__name__, str(e))}
            raise
        finally:
            return Response(
                response
            )

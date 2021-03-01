from unittest import TestCase, skip
from nlplib.facade import NlplibFacade


class LiabilityTest(TestCase):

    # @skip("Hanging Test ... so skip it for now")
    def test_no_liabilities(self):
        # Triplets of (document snippet, them_pary, you_party)
        no_liabs = [
            (
                'IN NO EVENT WILL WEST, ITS AFFILIATES OR ITS AGENTS BE LIABLE FOR ANY LOST PROFITS OR ANY CONSEQUENTIAL, EXEMPLARY, INCIDENTAL, INDIRECT OR SPECIAL DAMAGES, ARISING FROM OR IN ANY WAY RELATED TO THIS AGREEMENT OR RELATING IN WHOLE OR IN PART TO SUBSCRIBER\'S RIGHTS HEREUNDER OR THE USE OF OR INABILITY TO USE THE SERVICES, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.',
                'WEST', 'SUBSCRIBER'
            ),
            (
                'Customer will not hold Blackfoot responsible for, and Blackfoot will not be liable for, such approval or for violation of such policies.',
                'Blackfoot', 'Customer'
            ),
            (
                'Neither party will be liable to the other for any termination or expiration of this Agreement in accordance with its terms, however, expiration or termination will not extinguish claims or liability (including, without limitation, for payments due) arising prior to such expiration or termination.',
                'Blackfoot', 'Customer'
            ),
        ]
        # Tuples representing the lengths of NO_LIABILITY liabilities lists
        # for (them_party, you_party, both_parties)
        expected_lens = [
            (1, 0, 0),
            (1, 0, 0),
            (0, 0, 1), # is for both
        ]
        # Filters for NO_LIABILITY only
        filter_fn = lambda x: x[1] == 'NO_LIABILITY'


        # Run assertions for all defined examples
        for idx, (noli, them_party, you_party) in enumerate(no_liabs):
            facade = NlplibFacade(noli)
            actual_lens = (
                len(filter(filter_fn, facade.liabilities(them_party).iteritems())),
                len(filter(filter_fn, facade.liabilities(you_party).iteritems())),
                len(filter(filter_fn, facade.liabilities('both').iteritems())),
            )
            self.assertEqual(expected_lens[idx], actual_lens)

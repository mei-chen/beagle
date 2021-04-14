from unittest  import TestCase
from nlplib.facade import NlplibFacade


class ResponsibilityTest(TestCase):

    def test_dummy(self):
        # Triplets of (document snippet, them_pary, you_party)
        resp = [
            (
                'We must make available to you for your personal, non-commercial, use only.',
                'We', 'you'
            ),
        ]
        # Tuples representing the lengths of NO_LIABILITY responsibilities lists
        # for (them_party, you_party, both_parties)
        expected_lens = [
            (1, 0, 0),
        ]
        # Filters for NO_LIABILITY only
        filter_fn = lambda x: x[1].endswith('RESPONSIBILITY')


        # Run assertions for all defined examples
        for idx, (noli, them_party, you_party) in enumerate(resp):
            facade = NlplibFacade(noli, parties=(them_party, you_party, None))
            actual_lens = (
                len(list(filter(filter_fn, facade.responsibilities(them_party).items()))),
                len(list(filter(filter_fn, facade.responsibilities(you_party).items()))),
                len(list(filter(filter_fn, facade.responsibilities('both').items()))),
            )
            self.assertEqual(expected_lens[idx], actual_lens)

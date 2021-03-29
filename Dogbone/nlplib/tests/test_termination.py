from unittest import TestCase
from nlplib.facade import NlplibFacade


class TerminationTest(TestCase):

    def test_dummy(self):
        # Triplets of (document snippet, them_pary, you_party)
        term = [
            (
                'If COMPANY breaches the term(s) of this Agreement, STARBUCKS shall have the right to terminate this Agreement and/or demand the immediate return of all Confidential Information; (b) seek to recover its actual damages incurred by reason of such breach, including, without limitation, its attorneys fees and costs of suit; (c) seek to obtain injunctive relief to prevent such breach or to otherwise enforce the terms of this Agreement; and (d) pursue any other remedy available at law or in equity.',
                'STARBUCKS', 'you'
            ),
        ]
        # Tuples representing the lengths of NO_LIABILITY terminations lists
        # for (them_party, you_party, both_parties)
        expected_lens = [
            (1, 0, 0),
        ]
        # Filters for NO_LIABILITY only
        filter_fn = lambda x: x[1].endswith('TERMINATION')

        # Run assertions for all defined examples
        for idx, (noli, them_party, you_party) in enumerate(term):
            facade = NlplibFacade(noli, parties=(them_party, you_party, None))
            actual_lens = (
                len(filter(filter_fn, facade.terminations(them_party).items())),
                len(filter(filter_fn, facade.terminations(you_party).items())),
                len(filter(filter_fn, facade.terminations('both').items())),
            )
            self.assertEqual(expected_lens[idx], actual_lens)

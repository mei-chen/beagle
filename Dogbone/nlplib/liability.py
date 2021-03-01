from nlplib.generics import GenericAnalyzer
from nlplib.grammars import LIABILITIES_GRAMMAR, LIABILITIES_TYPES


class LiabilityAnalyzer(GenericAnalyzer):
    def __init__(self, wordtagged, mention_clusters, them_party, you_party):
        super(LiabilityAnalyzer, self).__init__(wordtagged, mention_clusters, them_party, you_party)

    @property
    def _analyzer_grammar(self):
        return LIABILITIES_GRAMMAR

    @property
    def _result_types(self):
        return LIABILITIES_TYPES

    @property
    def liabilities(self):
        return self.results

    def readable_liabilities(self, mention):
        return self.readable_results(mention)



def demo():
    from django.conf import settings
    from nlplib.coreference import MentionCluster
    from nlplib.utils import text2wordtag, preprocess_text
    from pprint import pprint

    text = """
Disclaimer of Warranties and Limitation of Liability

To the extent that portions of this Site provide users an opportunity to post and exchange information,
ideas and opinions (the "Postings"), please be advised that Postings do not necessarily reflect the views of
Nickelodeon. In no event shall Nickelodeon assume or have any responsibility or liability for any Postings or
for any claims, damages or losses resulting from their use and/or appearance on this Site.
You hereby represent and warrant that you have all necessary rights in and to all Postings you provide and all
information they contain and that such Postings shall not infringe any proprietary or other rights of third
parties or contain any libelous, tortious, or otherwise unlawful information.
You hereby authorize Nickelodeon to use, and authorize others to use, your Postings in whole or in part,
on a royalty-free basis, throughout the universe in perpetuity in any and all media, now known or hereafter
devised, alone, or together or as part of other material of any kind or nature. Without limiting the foregoing,
Nickelodeon will have the right to use and change the Postings in any manner that Nickelodeon may determine.
Additionally, Nickelodeon may sweep its chatrooms and/or message boards periodically in its sole discretion.
Nickelodeon does not allow Postings which contain:

Some of the E-Commerce Services utilize third party service providers.
All purchases made through these third party service providers are subject to their respective terms and conditions
of use. Additional information regarding the Nick Shop's third party service providers can be found here.
Nickelodeon is not responsible and has no liability whatsoever for goods or services you obtain through our third
party service providers or other web sites or web pages.
Waiver
"""

    settings.configure()
    analyzer = LiabilityAnalyzer(
        text2wordtag(preprocess_text(text)),
        [
            MentionCluster([
                {'form': 'You', 'type': 'PRONOUN_MENTION'},
            ]),
            MentionCluster([
                {'form': 'Nickelodeon', 'type': 'COMPANY_MENTION'},
            ]),
        ])

    # print analyzer.render_grammar(analyzer.mention_clusters[0])
    print analyzer.render_grammar(analyzer.mention_clusters[1])

    # pprint(analyzer._process_liabilities(analyzer.mention_clusters[0]))
    pprint(analyzer._process_liabilities(analyzer.mention_clusters[1]))

    pprint(analyzer.readable_liabilities)


if __name__ == "__main__":
    demo()

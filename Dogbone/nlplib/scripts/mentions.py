from nlplib.utils import preprocess_text, text2wordtag
from nlplib.utils import extract_nodes, tree2str
from pprint import pprint
from nlplib.coreference import CoreferenceResolution
from nlplib.mention import parse_mentions
import collections

text = """
End-User License Agreement

END-USER LICENSE AGREEMENT FOR "GIELTSHELP.COM" and "ACADEMICENGLISHHELP.COM"
IMPORTANT PLEASE READ THE TERMS AND CONDITIONS OF THIS LICENSE AGREEMENT CAREFULLY BEFORE
CONTINUING WITH ANY PRODUCT AND/OR SERVICE: 2THINK1 SOLUTIONS INC's End-User License Agreement ("EULA") is a legal agreement between you (either an individual or a single entity) and 2THINK1 SOLUTIONS INC for the 2THINK1 SOLUTIONS INC SOFTWARE PRODUCT(S) AND/OR WEBSITES identified above which may include associated software components, media, printed materials, and "online" or electronic documentation ("SOFTWARE PRODUCT(S) AND/OR WEBSITES"). By installing, copying, or otherwise using the SOFTWARE PRODUCT(S) AND/OR WEBSITES, you agree to be bound by the terms of this EULA. This license agreement represents the entire agreement concerning the program between you, 2THINK1SOLUTIONS INC, (referred to as "licenser"), and it supersedes any prior proposal, representation, or understanding between the parties. If you do not agree to the terms of this EULA, do not install or use the SOFTWARE PRODUCT(S) AND/OR WEBSITES. The SOFTWARE PRODUCT(S) AND/OR WEBSITES is protected by copyright laws and international copyright treaties, as well as other intellectual property laws and treaties. The SOFTWARE PRODUCT(S) AND/OR WEBSITES is licensed, not sold.
1. GRANT OF LICENSE.

The SOFTWARE PRODUCT(S) AND/OR WEBSITES is licensed as follows:
(a) Installation and Use.
2THINK1 SOLUTIONS INC grants you the right to install and use copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES on your computer running a validly licensed copy of the operating system for which the SOFTWARE PRODUCT(S) AND/OR WEBSITES was designed [e.g., Windows 95, Windows NT, Windows 98, Windows 2000, Windows 2003, Windows XP, Windows ME, Windows Vista].
(b) Backup Copies.
You may also make copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES as may be necessary for backup and archival purposes.
2. DESCRIPTION OF OTHER RIGHTS AND LIMITATIONS.

(a) Maintenance of Copyright Notices.
You must not remove or alter any copyright notices on any and all copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
(b) Distribution.
You may not distribute registered copies of the SOFTWARE PRODUCT(S) AND/OR WEBSITES to third parties. Evaluation versions available for download from 2THINK1 SOLUTIONS INC's websites may be freely distributed.
(c) Prohibition on Reverse Engineering, Decompilation, and Disassembly.
You may not reverse engineer, decompile, or disassemble the SOFTWARE PRODUCT(S) AND/OR WEBSITES, except and only to the extent that such activity is expressly permitted by applicable law notwithstanding this limitation.
(d) Rental.
You may not rent, lease, or lend the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
(e) Support Services.
2THINK1 SOLUTIONS INC may provide you with support services related to the SOFTWARE PRODUCT(S) AND/OR WEBSITES ("Support Services"). Any supplemental software code provided to you as part of the Support Services shall be considered part of the SOFTWARE PRODUCT(S) AND/OR WEBSITES and subject to the terms and conditions of this EULA.
(f) Compliance with Applicable Laws.
You must comply with all applicable laws regarding use of the SOFTWARE PRODUCT(S) AND/OR WEBSITES.
3. TERMINATION
"""


def demo():
    parsed_sentences = [parse_mentions(wt) for wt in text2wordtag(preprocess_text(text))]
    print parsed_sentences

    typed_mentions = collections.defaultdict(list)
    mention_types = ['PRONOUN_MENTION', 'COMPANY_MENTION', 'ENTITY_MENTION']
    for p_sent in parsed_sentences:
        for m_type in mention_types:
            typed_mentions[m_type].extend([tree2str(n) for n in extract_nodes(p_sent, m_type)])

    pprint(dict(typed_mentions))

    cr = CoreferenceResolution(parsed_sentences)
    cr.resolute()


if __name__ == "__main__":
    demo()
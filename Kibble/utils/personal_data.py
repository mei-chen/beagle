# -*- coding: utf-8 -*-

import codecs
import os
import re
import time
import zipfile
from collections import defaultdict, OrderedDict
from copy import copy
from random import randrange
from io import BytesIO

import chardet
import Stemmer
import spacy
from bs4 import BeautifulSoup
from marisa_trie import Trie

from document.models import PersonalData, CustomPersonalData
from utils.sentence_splitting.api import SentenceSplittingRemoteAPI

stemmer = Stemmer.Stemmer('english')

DOCX_TEXT_RELS_FILES = [
    'docProps/core.xml',
    'docProps/app.xml',
    'word/document.xml',
    'word/comments.xml',
    '_rels/.rels',
    'word/_rels/document.xml.rels'
]

CURR_CODES = ['AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BOV', 'BRL', 'BSD', 'BTN', 'BWP', 'BYR', 'BZD', 'CAD', 'CDF', 'CHE', 'CHF', 'CHW', 'CLF', 'CLP', 'CNY', 'COP', 'COU', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 'IDR', 'ILS', 'INR', 'IQD', 'IRR', 'ISK', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRU', 'MUR', 'MVR', 'MWK', 'MXN', 'MXV', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'ROL', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'SSP', 'STN', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'USN', 'UYI', 'UYU', 'UZS', 'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XCD', 'XDR', 'XOF', 'XPF', 'XSU', 'XUA', 'YER', 'ZAR', 'ZMW', 'ZWL']
DOLLAR_TYPES = ['australian', 'bahamian', 'barbados', 'belize', 'bermudian', 'brunei', 'canadian', 'cayman islands', 'east caribbean', 'fiji', 'guyana', 'hong kong', 'jamaican', 'liberian', 'namibia', 'new taiwan', 'new zealand', 'singapore', 'solomon islands', 'suriname', 'trinidad and tobago', 'us', 'zimbabwe']

year_short = '(?:[0-9]{2})'
year_full = '(?:(?:19|20)[0-9]{2})'
month = '(?:0[1-9]|1[0-2])'
day = '(?:0[1-9]|[12][0-9]|3[01])'

def date_pattern(*args, **kwargs):
    # The actual order of day, month, year may change
    assert len(args) == 3
    delimiter = kwargs.get('delimiter', '')
    escape = kwargs.get('escape', True)
    if escape:
        delimiter = re.escape(delimiter)
    return r'{}{d}{}{d}{}'.format(*args, d=delimiter)

REGEX_PATTERNS = {
    'Date': (
        re.compile(
            r'\b(?<!:)(?<!:\d)[0-3]?\d(?:st|nd|rd|th)?\s+(?:of\s+)?(?:jan\.?|january|feb\.?|february|mar\.?|march|apr\.?|april|may|jun\.?|june|jul\.?|july|aug\.?|august|sep\.?|september|oct\.?|october|nov\.?|november|dec\.?|december)(?:(?:,\s*|\s+)\d{4})?\b|\b(?:jan\.?|january|feb\.?|february|mar\.?|march|apr\.?|april|may|jun\.?|june|jul\.?|july|aug\.?|august|sep\.?|september|oct\.?|october|nov\.?|november|dec\.?|december)(?:\s+(?<!:)(?<!:\d)[0-3]?\d(?:st|nd|rd|th)?(?:(?:,\s*|\s+)\d{4})?|(?:(?:,\s*|\s+)\d{4}))\b|(?<![\w/.-])[0-3]?\d[-./][0-3]?\d[-./]\d{2,4}(?![\w/-])', re.IGNORECASE
        ),
    ),

    'Phone': (
        re.compile(
            r'(?<!\S)(?:\+[1-9]\d{0,2}[ -]?)?(?:\d{3}[ -]?|\(\d{3}\)[ -]?)?\d{3}([ -]?)(?:\d{4}|\d{2}\1\d{2})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Link': (
        re.compile(
            u'\\b(?:https?://|www\d{0,3}[.])?(?<!@)[a-z0-9.\-]+[.](?:(?:international)|(?:construction)|(?:contractors)|(?:enterprises)|(?:photography)|(?:immobilien)|(?:management)|(?:technology)|(?:directory)|(?:education)|(?:equipment)|(?:institute)|(?:marketing)|(?:solutions)|(?:builders)|(?:clothing)|(?:computer)|(?:democrat)|(?:diamonds)|(?:graphics)|(?:holdings)|(?:lighting)|(?:plumbing)|(?:training)|(?:ventures)|(?:academy)|(?:careers)|(?:company)|(?:domains)|(?:florist)|(?:gallery)|(?:guitars)|(?:holiday)|(?:kitchen)|(?:recipes)|(?:shiksha)|(?:singles)|(?:support)|(?:systems)|(?:agency)|(?:berlin)|(?:camera)|(?:center)|(?:coffee)|(?:estate)|(?:kaufen)|(?:luxury)|(?:monash)|(?:museum)|(?:photos)|(?:repair)|(?:social)|(?:tattoo)|(?:travel)|(?:viajes)|(?:voyage)|(?:build)|(?:cheap)|(?:codes)|(?:dance)|(?:email)|(?:glass)|(?:house)|(?:ninja)|(?:photo)|(?:shoes)|(?:solar)|(?:today)|(?:aero)|(?:arpa)|(?:asia)|(?:bike)|(?:buzz)|(?:camp)|(?:club)|(?:coop)|(?:farm)|(?:gift)|(?:guru)|(?:info)|(?:jobs)|(?:kiwi)|(?:land)|(?:limo)|(?:link)|(?:menu)|(?:mobi)|(?:moda)|(?:name)|(?:pics)|(?:pink)|(?:post)|(?:rich)|(?:ruhr)|(?:sexy)|(?:tips)|(?:wang)|(?:wien)|(?:zone)|(?:biz)|(?:cab)|(?:cat)|(?:ceo)|(?:com)|(?:edu)|(?:gov)|(?:int)|(?:mil)|(?:net)|(?:onl)|(?:org)|(?:pro)|(?:red)|(?:tel)|(?:uno)|(?:xxx)|(?:ac)|(?:ad)|(?:ae)|(?:af)|(?:ag)|(?:ai)|(?:al)|(?:am)|(?:an)|(?:ao)|(?:aq)|(?:ar)|(?:as)|(?:at)|(?:au)|(?:aw)|(?:ax)|(?:az)|(?:ba)|(?:bb)|(?:bd)|(?:be)|(?:bf)|(?:bg)|(?:bh)|(?:bi)|(?:bj)|(?:bm)|(?:bn)|(?:bo)|(?:br)|(?:bs)|(?:bt)|(?:bv)|(?:bw)|(?:by)|(?:bz)|(?:ca)|(?:cc)|(?:cd)|(?:cf)|(?:cg)|(?:ch)|(?:ci)|(?:ck)|(?:cl)|(?:cm)|(?:cn)|(?:co)|(?:cr)|(?:cu)|(?:cv)|(?:cw)|(?:cx)|(?:cy)|(?:cz)|(?:de)|(?:dj)|(?:dk)|(?:dm)|(?:do)|(?:dz)|(?:ec)|(?:ee)|(?:eg)|(?:er)|(?:es)|(?:et)|(?:eu)|(?:fi)|(?:fj)|(?:fk)|(?:fm)|(?:fo)|(?:fr)|(?:ga)|(?:gb)|(?:gd)|(?:ge)|(?:gf)|(?:gg)|(?:gh)|(?:gi)|(?:gl)|(?:gm)|(?:gn)|(?:gp)|(?:gq)|(?:gr)|(?:gs)|(?:gt)|(?:gu)|(?:gw)|(?:gy)|(?:hk)|(?:hm)|(?:hn)|(?:hr)|(?:ht)|(?:hu)|(?:id)|(?:ie)|(?:il)|(?:im)|(?:in)|(?:io)|(?:iq)|(?:ir)|(?:is)|(?:it)|(?:je)|(?:jm)|(?:jo)|(?:jp)|(?:ke)|(?:kg)|(?:kh)|(?:ki)|(?:km)|(?:kn)|(?:kp)|(?:kr)|(?:kw)|(?:ky)|(?:kz)|(?:la)|(?:lb)|(?:lc)|(?:li)|(?:lk)|(?:lr)|(?:ls)|(?:lt)|(?:lu)|(?:lv)|(?:ly)|(?:ma)|(?:mc)|(?:md)|(?:me)|(?:mg)|(?:mh)|(?:mk)|(?:ml)|(?:mm)|(?:mn)|(?:mo)|(?:mp)|(?:mq)|(?:mr)|(?:ms)|(?:mt)|(?:mu)|(?:mv)|(?:mw)|(?:mx)|(?:my)|(?:mz)|(?:na)|(?:nc)|(?:ne)|(?:nf)|(?:ng)|(?:ni)|(?:nl)|(?:no)|(?:np)|(?:nr)|(?:nu)|(?:nz)|(?:om)|(?:pa)|(?:pe)|(?:pf)|(?:pg)|(?:ph)|(?:pk)|(?:pl)|(?:pm)|(?:pn)|(?:pr)|(?:ps)|(?:pt)|(?:pw)|(?:py)|(?:qa)|(?:re)|(?:ro)|(?:rs)|(?:ru)|(?:rw)|(?:sa)|(?:sb)|(?:sc)|(?:sd)|(?:se)|(?:sg)|(?:sh)|(?:si)|(?:sj)|(?:sk)|(?:sl)|(?:sm)|(?:sn)|(?:so)|(?:sr)|(?:st)|(?:su)|(?:sv)|(?:sx)|(?:sy)|(?:sz)|(?:tc)|(?:td)|(?:tf)|(?:tg)|(?:th)|(?:tj)|(?:tk)|(?:tl)|(?:tm)|(?:tn)|(?:to)|(?:tp)|(?:tr)|(?:tt)|(?:tv)|(?:tw)|(?:tz)|(?:ua)|(?:ug)|(?:uk)|(?:us)|(?:uy)|(?:uz)|(?:va)|(?:vc)|(?:ve)|(?:vg)|(?:vi)|(?:vn)|(?:vu)|(?:wf)|(?:ws)|(?:ye)|(?:yt)|(?:za)|(?:zm)|(?:zw))(?:/[^\s()<>]+[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019])?\\b', re.IGNORECASE
        ),
    ),

    'Email': (
        re.compile(
            u"([a-z0-9!#$%&'*+\/=?^_`{|.}~-]+@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)", re.IGNORECASE
        ),
    ),

    'IP': (
        re.compile(
            r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b', re.UNICODE
        ),
    ),

    # 'Price': (
    #     # Optional currency symbol, mandatory currency code (233.4 USD)
    #     re.compile(
    #         ur'(?i)(?:[$¥£€₽₴¢₡₪₩₮฿₱؋]\s*)?[+-]?[0-9]{1,12}(?:,?[0-9]{3})*(?:\.[0-9]{1,6})?\s*(?:' + '|'.join(CURR_CODES) + ')'
    #     ),
    #     # Optional currency symbol, mandatory dollar type (233.4 Australian dollars)
    #     re.compile(
    #         ur'(؋]\s*)?[+-]?[0-9]{1,12}(?:,?[0-9]{3})*(?:\.[0-9]{1,6})?\s+(?:' + '|'.join(DOLLAR_TYPES) + ')\s+dollars?'
    #     ),
    #     # Mandatory currency symbol ($233.4 or 233.4$)
    #     re.compile(
    #         ur'[$¥£€₽₴¢₡₪₩₮฿₱؋]\s*[+-]?[0-9]{1,12}(?:,?[0-9]{3})*(?:\.[0-9]{1,6})?|[+-]?[0-9]{1,12}(?:,?[0-9]{3})*(?:\.[0-9]{1,6})?\s*[$¥£€₽₴¢₡₪₩₮฿₱؋]'
    #     ),
    # ),

    # Not working properly anyway, so disable for now
    # 'Street Address': (
    #     re.compile(
    #         u'\d{1,4} [\w\s]{1,20}(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir)\W?(?=\s|$)', re.IGNORECASE
    #     ),
    # ),

    'Salutation': (
        re.compile(
            r'(?<![\w.])(?:Mr[.]?|Mrs[.]?|Ms[.]?|Miss)(?![\w.])', re.UNICODE
        ),
    ),

    'Sexual Orientation': (
        re.compile(
            r'\b(?:heterosexuality|heterosexuals?|homosexuality|homosexuals?|gays?|lesbians?|bisexuality|bisexuals?|androsexuality|androsexuals?|androphilia|androphillic|gynesexuality|gynesexuals?|gynephilia|gynephillic|pansexuality|pansexuals?|omnisexuals?|asexuality|asexuals?)\b', re.IGNORECASE | re.UNICODE
        ),
    ),

    # Some kinds of identity numbers
    # (too weak and vague patterns leading to many mismatches are commented out)

    'ABA Routing Number': (
        re.compile(
            r'(?<!\S)[0123678](?:\d{3}-\d{4}-\d|\d{8})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Argentina National Identity Number': (
        re.compile(
            r'(?<!\S)\d{2}\.\d{3}\.\d{3}(?=[\s,;]|$)', re.UNICODE
        ),
    ),

    'Australia Medical Account Number': (
        re.compile(
            r'(?<!\S)[2-6]\d{10}\d?(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Australia Passport Number': (
        re.compile(
            r'(?<!\S)[A-Z]\d{7}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Brazil Legal Entity Number': (
        re.compile(
            r'(?<!\S)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}(?=[\s,;]|$)', re.UNICODE
        ),
    ),

    'Brazil National ID Card Number': (
        re.compile(
            r'(?<!\S)(?:\d{2}\.\d{3}\.\d{3}-\d|\d{10}-\d)(?=[\s,;]|$)', re.UNICODE
        ),
    ),

    'Canada Health Service Number': (
        re.compile(
            r'(?<!\S)\d{10}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Canada Passport Number': (
        re.compile(
            r'(?<!\S)[A-Z]{2}\d{6}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Canada Personal Health Identification Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Canada Social Insurance Number': (
        re.compile(
            r'(?<!\S)(?:\d{3}-\d{3}-\d{3}|\d{3} \d{3} \d{3}|\d{9})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Chile Identity Card Number': (
        re.compile(
            r'(?<!\S)\d{1,2}\.\d{3}\.\d{3}-[a-z\d](?=[\s,;]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'China Resident Identity Card Number': (
        re.compile(
            r'(?<!\S)\d{6}%s\d{3}\d(?=[\s,;.]|$)' % date_pattern(year_full, month, day), re.UNICODE
        ),
    ),

    'Croatia Identity Card Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Croatia Personal Identification Number': (
        re.compile(
            r'(?<!\S)%s\d{4}(?=[\s,;.]|$)' % date_pattern(day, month, year_short), re.UNICODE
        ),
    ),

    'Czech National Identity Card Number': (
        re.compile(
            r'(?<!\S)\d{6}/\d{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Denmark Personal Identification Number': (
        re.compile(
            r'(?<!\S)%s-\d{4}(?=[\s,;.]|$)' % date_pattern(day, month, year_short), re.UNICODE
        ),
    ),

    'Drug Enforcement Agency Number': (
        re.compile(
            r'(?<!\S)[abcdefghjklmnprstux][a-z]\d{7}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Finland National ID Number': (
        re.compile(
            r'(?<!\S)%s[a+-]\d{3}[a-z\d](?=[\s,;.]|$)' % date_pattern(day, month, year_short), re.IGNORECASE | re.UNICODE
        ),
    ),

    'Finland Passport Number': (
        re.compile(
            r'(?<!\S)[A-Z]{2}\d{7}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'France National ID Card Number': (
        re.compile(
            r'(?<!\S)\d{12}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'France Passport Number': (
        re.compile(
            r'(?<!\S)\d{2}[A-Z]{2}\d{5}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'France Social Security Number': (
        re.compile(
            r'(?<!\S)\d{13} ?\d{2}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Germany Driver License Number': (
        re.compile(
            r'(?<!\S)[a-z\d]\d{2}[a-z\d]{6}\d[a-z\d](?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Germany Identity Card Number': (
        re.compile(
            r'(?<!\S)(?:[a-z]\d{8}|\d{10})(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Germany Passport Number': (
        re.compile(
            r'(?<!\S)[CFGHJK\d]\d{3}[CF-HJ-NPRTV-Z\d]{5}\d(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    # 'Greece National ID Card Number': (
    #     re.compile(
    #         ur'(?<!\S)(?:[Α-Ω]-\d{6}|[ABEZHIKMNOPTYX]{2}-\d{6})(?=[\s,;.]|$)', re.UNICODE
    #     ),
    # ),

    'Hong Kong Identity Card Number': (
        re.compile(
            r'(?<!\S)[A-Z]{1,2}\d{6}(?:[A\d]|\([A\d]\))(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'India Permanent Account Number': (
        re.compile(
            r'(?<!\S)[A-Z]{5}\d{4}[A-Z](?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    # 'India Unique Identification Number': (
    #     re.compile(
    #         r'(?<!\S)(?:\d{4}-\d{4}-\d{4}|\d{4} \d{4} \d{4}|\d{12})(?=[\s,;.]|$)', re.UNICODE
    #     ),
    # ),

    'Indonesia Identity Card Number': (
        re.compile(
            r'(?<!\S)\d{2}\.?\d{2}\d{2}\.?%s\.?\d{4}(?=[\s,;]|$)' % date_pattern(day, month, year_short), re.UNICODE
        ),
    ),

    'International Banking Account Number': (
        re.compile(
            r'(?<!\S)(?:ad|ae|al|at|az|ba|be|bg|bh|br|by|ch|cr|cy|cz|de|dk|do|ee|es|fi|fo|fr|gb|ge|gi|gl|gr|gt|hr|hu|ie|il|iq|is|it|jo|kw|kz|lb|lc|li|lt|lu|lv|mc|md|me|mk|mr|mt|mu|nl|no|pl|pk|ps|pt|qa|ro|rs|sa|sc|se|si|sk|sm|st|sv|tl|tn|tr|ua|vg|xk) ?\d{2}(?: ?[a-z\d]{4}){1,7}(?: ?[a-z\d]{1,3})?(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Ireland Personal Public Service Number': (
        re.compile(
            r'(?<!\S)(?:\d{7}[A-Z]{2}|\d{7}[A-Z][AH])(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Israel Bank Account Number': (
        re.compile(
            r'(?<!\S)\d{2}-\d{3}-\d{8}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Israel National ID Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    # 'Italy Driver License Number': (
    #     re.compile(
    #         r'(?<!\S)[A-Z][AV][A-Z\d_]{7}[A-Z](?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
    #     ),
    # ),

    'Japan Driver License Number': (
        re.compile(
            r'(?<!\S)\d{12}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Japan Passport Number': (
        re.compile(
            r'(?<!\S)[A-Z]{2}\d{7}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Japan Resident Registration Number': (
        re.compile(
            r'(?<!\S)\d{11}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Malaysia ID Card Number': (
        re.compile(
            r'(?<!\S)%s-\d{2}-\d{3}\d(?=[\s,;.]|$)' % date_pattern(year_short, month, day), re.UNICODE
        ),
    ),

    'New Zealand Ministry of Health Number': (
        re.compile(
            r'(?<!\S)[A-Z]{3} ?\d{4}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Norway Identification Number': (
        re.compile(
            r'(?<!\S)%s\d{3}\d{2}(?=[\s,;.]|$)' % date_pattern(day, month, year_short), re.UNICODE
        ),
    ),

    'Philippines Unified Multi-Purpose ID Number': (
        re.compile(
            r'(?<!\S)\d{4}-\d{7}-\d(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Poland Identity Card Number': (
        re.compile(
            r'(?<!\S)[A-Z]{3}\d{6}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Poland National ID Number': (
        re.compile(
            r'(?<!\S)\d{11}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Poland Passport Number': (
        re.compile(
            r'(?<!\S)[A-Z]{2}\d{7}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    # 'Portugal Citizen Card Number': (
    #     re.compile(
    #         r'(?<!\S)\d{8}(?=[\s,;.]|$)', re.UNICODE
    #     ),
    # ),

    'Saudi Arabia National ID Number': (
        re.compile(
            r'(?<!\S)\d{10}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Singapore National Registration Identity Card Number': (
        re.compile(
            r'(?<!\S)[FGST]\d{7}[A-Z](?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'South Africa Identification Number': (
        re.compile(
            r'(?<!\S)%s\d{4}\d[89]\d(?=[\s,;.]|$)' % date_pattern(year_short, month, day), re.UNICODE
        ),
    ),

    'South Korea Resident Registration Number': (
        re.compile(
            r'(?<!\S)%s-\d\d{4}\d\d(?=[\s,;.]|$)' % date_pattern(year_short, month, day), re.UNICODE
        ),
    ),

    'Spain Social Security Number': (
        re.compile(
            r'(?<!\S)\d{2}/\d{7,8}/\d{2}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Sweden National ID Number': (
        re.compile(
            r'(?<!\S)%s-\d{4}(?=[\s,;.]|$)' % date_pattern(year_short, month, day), re.UNICODE
        ),
    ),

    # 'Sweden Passport Number': (
    #     re.compile(
    #         r'(?<!\S)\d{8}(?=[\s,;.]|$)', re.UNICODE
    #     ),
    # ),

    'Taiwan National ID Number': (
        re.compile(
            r'(?<!\S)[A-Z][12]\d{8}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'Taiwan Passport Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Taiwan Resident Certificate Number': (
        re.compile(
            r'(?<!\S)[A-Z]{2}\d{8}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    # 'UK Electoral Roll Number': (
    #     re.compile(
    #         r'(?<!\S)[A-Z]{2}\d{1,4}(?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
    #     ),
    # ),

    'UK National Health Service Number': (
        re.compile(
            r'(?<!\S)(?:\d{3}|\d{10}) \d{3} \d{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'UK National Insurance Number': (
        re.compile(
            r'(?<!\S)(?!BG)(?!GB)(?!KN)(?!NK)(?!NT)(?!TN)(?!ZZ)[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]([ -]?)\d{2}\1\d{2}\1\d{2}\1[A-D](?=[\s,;.]|$)', re.IGNORECASE | re.UNICODE
        ),
    ),

    'UK Passport Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    # 'USA Bank Account Number': (
    #     re.compile(
    #         r'(?<!\S)\d{4,17}(?=[\s,;.]|$)', re.UNICODE
    #     ),
    # ),

    'USA Individual Taxpayer Identification Number': (
        re.compile(
            r'(?<!\S)(?:9\d{2}-[78]\d-\d{4}|9\d{2} [78]\d \d{4}|9\d{2}[78]\d{5})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'USA Passport Number': (
        re.compile(
            r'(?<!\S)\d{9}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'USA Social Security Number': (
        re.compile(
            r'(?<!\S)(?:\d{3}-\d{2}-\d{4}|\d{3} \d{2} \d{4}|\d{9})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    # Some types of credit cards

    'American Express Card': (
        re.compile(  # 15: 4-6-5
            r'(?<!\S)3[47][0-9]{2}([ -]?)[0-9]{6}\1[0-9]{5}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'BC Global Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:6541|6556)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'BankCard': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5610([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5602([ -]?)2[1-5][0-9]{2}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Dankort Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5019([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Diners Club Carte Blanche Card': (
        re.compile(  # 14: 4-6-4
            r'(?<!\S)30[0-5][0-9]([ -]?)[0-9]{6}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 14: 5-4-5
            r'(?<!\S)30[0-5][0-9]{2}([ -]?)[0-9]{4}\1[0-9]{5}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Diners Club International Card': (
        re.compile(  # 14: 4-6-4
            r'(?<!\S)(?:30[0-59][0-9]|36[0-9]{2})([ -]?)[0-9]{6}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 14: 5-4-5
            r'(?<!\S)(?:30[0-59][0-9]{2}|36[0-9]{3})([ -]?)[0-9]{4}\1[0-9]{5}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)3[89][0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 5-4-7
            r'(?<!\S)3[89][0-9]{3}([ -]?)[0-9]{4}\1[0-9]{7}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Diners Club enRoute Card': (
        re.compile(  # 15: 4-7-4
            r'(?<!\S)(?:2014|2149)([ -]?)[0-9]{7}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 15: 5-4-6
            r'(?<!\S)(?:2014|2149)[0-9]([ -]?)[0-9]{4}\1[0-9]{6}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Diners Club United States & Canada Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5[45][0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Discover Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:6011|64[4-9][0-9]|65[0-9]{2})([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)6221([ -]?)2[6-9][0-9]{2}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)6221([ -]?)[3-9][0-9]{3}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)622[2-8]([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)6229([ -]?)[01][0-9]{3}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)6229([ -]?)2[0-5][0-9]{2}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'InstaPayment Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)63[7-9][0-9]([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'InterPayment Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)636[0-9]([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 17-19: grouping pattern not known
            r'(?<!\S)636[0-9]{14,16}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'JCB Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)35(?:2[89]|[3-8][0-9])([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Laser Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:6304|6706|6709|6771)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 17-19: grouping pattern not known
            r'(?<!\S)(?:6304|6706|6709|6771)[0-9]{13,15}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Maestro Card': (
        re.compile(  # 13: 4-4-5
            r'(?<!\S)(?:50|5[6-8]|6[0-9])[0-9]{2}([ -]?)[0-9]{4}\1[0-9]{5}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 15: 4-6-5
            r'(?<!\S)(?:50|5[6-8]|6[0-9])[0-9]{2}([ -]?)[0-9]{6}\1[0-9]{5}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:50|5[6-8]|6[0-9])[0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 19: 4-4-4-4-3
            r'(?<!\S)(?:50|5[6-8]|6[0-9])[0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}\1[0-9]{3}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 12, 14, 17, 18: grouping pattern not known
            r'(?<!\S)(?:50|5[6-8]|6[0-9])(?:[0-9]{10}|[0-9]{12}|[0-9]{15}|[0-9]{16})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'MasterCard': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5[1-5][0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Solo Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:6334|6767)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 19: 4-4-4-4-3
            r'(?<!\S)(?:6334|6767)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}\1[0-9]{3}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 18: grouping pattern not known
            r'(?<!\S)(?:6334|6767)[0-9]{14}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Switch Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)(?:4903|4905|4911|4936|6333|6759)([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)5641([ -]?)82[0-9]{2}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)6331([ -]?)10[0-9]{2}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 18-19: grouping pattern not known
            r'(?<!\S)(?:4903|4905|4911|4936|6333|6759)[0-9]{14,15}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 18-19: grouping pattern not known
            r'(?<!\S)(?:564182|633110)[0-9]{12,13}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'UATP Card': (
        re.compile(  # 15: 3-4-4-4
            r'(?<!\S)1[0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 15: 4-5-6
            r'(?<!\S)1[0-9]{3}([ -]?)[0-9]{5}\1[0-9]{6}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'UnionPay Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)62[0-9]{2}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 19: 6-13
            r'(?<!\S)62[0-9]{4}([ -]?)[0-9]{13}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 17-18: grouping pattern not known
            r'(?<!\S)62[0-9]{15,16}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Visa Card': (
        re.compile(  # 16: 4-4-4-4
            r'(?<!\S)4[0-9]{3}([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{4}(?=[\s,;.]|$)', re.UNICODE
        ),
        re.compile(  # 13-15, 17-19: grouping pattern not known
            r'(?<!\S)4(?:[0-9]{12,14}|[0-9]{16,18})(?=[\s,;.]|$)', re.UNICODE
        ),
    ),

    'Voyager Card': (
        re.compile(  # 15: 4-4-4-3
            r'(?<!\S)8699([ -]?)[0-9]{4}\1[0-9]{4}\1[0-9]{3}(?=[\s,;.]|$)', re.UNICODE
        ),
    ),
}

# The labels and their descriptions (from the official spaCy documentation)
SPACY_LABELS = {
    'PERSON': 'Person',  # People, including fictional.
    'NORP': 'Group',  # Nationalities or religious or political groups.
    'GPE': 'Location',  # Countries, cities, states.
}

NLP = None
EN = None

text_strip_re = re.compile(r'^[\W_]*(.*?)[\W_]*$', re.DOTALL | re.UNICODE)
reducible_chars_re = re.compile(u'[0-9,\(\)\[\]\.\-]+', re.UNICODE)
ws_re = re.compile(u'\s+', re.UNICODE)

split_sents = SentenceSplittingRemoteAPI(None).process_text

# TODO:
# Driver license
# health number
# passport number

# Organization


def contentsdecode(text):
    found_encoding = chardet.detect(text)['encoding']
    dec_contents = text.decode(found_encoding or 'utf-8')
    return dec_contents


def gather_by_regex(text):
    """
    Here we gather everything from REGEX_PATTERNS.
    """

    result = []

    for type, patterns in REGEX_PATTERNS.items():
        matches = defaultdict(set)

        for pattern in patterns:
            for match_obj in pattern.finditer(text):
                entity = match_obj.group()
                start_end = match_obj.span()

                matches[entity].add(start_end)

        for entity, positions in matches.items():
            positions = sorted(positions)

            # Leave the first occurrence so far
            # (the size of the PersonalData.location field is restricted)
            location = '%s:%s' % positions[0]
            # location = ', '.join(
            #     '%s:%s' % start_end for start_end in positions
            # )

            result.append((type, entity, 'Text: %s' % location))

    return result


def _init_nlp():
    global NLP

    if NLP is None:
        NLP = spacy.load('en_core_web_md')


def _init_en():
    global EN

    if EN is None:
        filename = os.path.join(os.path.dirname(__file__), 'data', 'en_stems.csv')
        with codecs.open(filename, mode='rb', encoding='utf-8') as en:
            words = [word.strip() for word in en]
            EN = Trie(words)


def _strip_text(text):
    return text_strip_re.match(text).group(1)


def _is_common_word(word):
    _init_en()

    word = _strip_text(word.lower())
    is_common = stemmer.stemWord(word) in EN
    return is_common


def gather_by_spacy(text):
    """
    Here we gather everything from SPACY_LABELS.
    """

    def _has_only_common_words(text):
        alpha = reducible_chars_re.sub(' ', text)
        alpha_clean = ws_re.sub(' ', alpha).strip()
        return all(_is_common_word(w) for w in alpha_clean.split())

    _init_nlp()
    result = []

    # For each found entity store all detected labels
    # in order to fix possible collisions later
    entities = OrderedDict()

    for clause in text.split('\n'):
        if not clause:
            continue

        model = NLP(clause)
        for ent in model.ents:
            if ent.label_ in SPACY_LABELS:
                lb = SPACY_LABELS[ent.label_]
                t = _strip_text(ent.text)
                if not t:
                    continue

                # Some types of labels are detected well enough (rarely,
                # but accurately), but some are much harder to detect,
                # so some post-processing and filtering may be needed
                dict_check = lb not in ['Group', 'Location']

                if lb == 'Location':
                    if len(ent) == 1:
                        # A single word should be checked in the dictionary;
                        # for two or more words the dictionary may not help
                        # (e.g., Mountain View)
                        dict_check = True
                    elif t.startswith('the'):
                        t = t[3:].strip()

                # Skip all entities where all words are common
                if dict_check and _has_only_common_words(t):
                    continue

                if t not in entities:
                    entities[t] = set()

                entities[t].add(lb)

    labels_priorities = {
        'Group': 3,
        'Location': 2,
        'Person': 1,
    }

    for t in entities:
        ls = list(entities[t])
        # Try to decide which label is more probable
        # according to the priorities of the labels
        # E.g., if Ontario is detected as both Person and Location,
        # then we will prefer Location rather than Person
        if len(ls) > 1:
            ls.sort(key=labels_priorities.__getitem__, reverse=True)
        l = ls[0]

        positions = []

        i = 0
        while True:
            start = text.find(t, i)
            if start == -1:
                break
            end = start + len(t)
            start_end = (start, end)
            positions.append(start_end)
            i = end
            break  # delete this line in order to find all positions

        # Leave the first occurrence so far
        # (the size of the PersonalData.location field is restricted)
        location = '%s:%s' % positions[0]
        # location = ', '.join(
        #     '%s:%s' % start_end for start_end in positions
        # )

        result.append((l, t, 'Text: %s' % location))

    return result


def gather_from_doc_meta(props_core, props_app):
    result = []
    if props_app and props_app.find('Company'):
        result.append((
            'Organization',
            props_app.find('Company').text,
            'Metadata'
        ))
    if props_core and props_core.find('creator'):
        result.append((
            'Person',
            props_core.find('creator').text,
            'Metadata'
        ))
    if props_core and props_core.find('lastModifiedBy'):
        result.append((
            'Person',
            props_core.find('lastModifiedBy').text,
            'Metadata'
        ))

    return result


def extract_text_from_docx_tree(root):
    text = []
    for node in root.recursiveChildGenerator():
        name = getattr(node, 'name', None)
        if name is not None:  # tag
            if name == 't':
                text.append(node.string)
            elif name in ('br', 'p'):
                text.append('\n')
            elif name == 'tab':
                text.append('\t')
    return ''.join(text)


def find_personal_data(instance):
    with zipfile.ZipFile(instance.content_file, mode='r') as zin:
        props_core = props_app = None
        if 'docProps/core.xml' in zin.namelist():
            props_core_text = contentsdecode(zin.read('docProps/core.xml'))
            props_core = BeautifulSoup(props_core_text, 'xml')
        if 'docProps/app.xml' in zin.namelist():
            props_app_text = contentsdecode(zin.read('docProps/app.xml'))
            props_app = BeautifulSoup(props_app_text, 'xml')

        doc_text = contentsdecode(zin.read('word/document.xml'))
        doc = BeautifulSoup(doc_text, 'xml')
        text = extract_text_from_docx_tree(doc)

    result = gather_from_doc_meta(props_core, props_app)

    start = time.time()
    result.extend(gather_by_regex(text))
    end = time.time()
    print('REGEX: %.3fs' % (end - start))

    start = time.time()
    result.extend(gather_by_spacy(text))
    end = time.time()
    print('SPACY: %.3fs' % (end - start))

    return result


def find_personal_data_in_text(text):
    start = time.time()
    result = gather_by_regex(text)
    end = time.time()
    print('REGEX: %.3f' % (end - start))

    start = time.time()
    result.extend(gather_by_spacy(text))
    end = time.time()
    print('SPACY: %.3f' % (end - start))

    return result


def obfuscate_text(obf_str, text, replacements):
    text = contentsdecode(text)

    for phrase, pd_type, obf_type in replacements:
        if obf_type == 'highlight':
            continue

        if pd_type == 'rgx':
            compiled = re.compile(phrase)
            found = compiled.findall(text)
            for phrase in found:
                if obf_type == 'black_out':
                    obf_len = len(phrase) + randrange(1, 8)
                    text = text.replace(phrase, u'\u25A0' * obf_len)
                else:
                    text = text.replace(phrase, obf_str)
        elif obf_type == 'black_out':
            obf_len = len(phrase) + randrange(1, 8)
            text = text.replace(phrase, u'\u25A0' * obf_len)
        else:
            text = text.replace(phrase, obf_str)

    return text.encode('utf-8')


def obfuscate_sents(obf_str, highlight_color, text, sents):
    text = contentsdecode(text)
    parsed = BeautifulSoup(text, 'xml')

    for p in parsed.find_all('w:p'):
        splitted = None
        for obf_sent, obf_type in sents:
            if len(obf_sent) > len(p.text.strip()):
                continue

            if not splitted:
                success, splitted = split_sents(p.text)
            if not success:
                print(splitted)
                continue

            for s in splitted:
                if s != obf_sent:
                    continue

                if obf_type in ['string', 'black_out']:
                    old_string = p.text
                    for r in p.find_all('w:r')[1:]:
                        r.decompose()
                    p.find('w:r').find('w:t').decompose()
                    t = parsed.new_tag('w:t')
                    if obf_type == 'black_out':
                        obf_len = len(s) + randrange(1, 8)
                        new_string = old_string.replace(s, u'\u25A0' * obf_len)
                    elif obf_type == 'string':
                        new_string = old_string.replace(s, obf_str)
                    t.string = new_string
                    p.find('w:r').append(t)

                elif obf_type == 'highlight':
                    p_text = p.text
                    text_before = p_text[:p_text.find(s)]
                    text_after = p_text[p_text.rfind(s) + len(s):]
                    for r in p.find_all('w:r')[1:]:
                        r.decompose()
                    r = p.find('w:r')
                    r.find('w:t').decompose()

                    if text_before:
                        r_before = copy(r)
                        t = parsed.new_tag('w:t')
                        t.string = text_before
                        r_before.append(t)
                        r.insert_before(r_before)
                    if text_after:
                        r_after = copy(r)
                        t = parsed.new_tag('w:t')
                        t.string = text_after
                        r_after.append(t)
                        r.insert_after(r_after)

                    t = parsed.new_tag('w:t')
                    t.string = s
                    r.append(t)
                    highlight_tag = parsed.new_tag('w:highlight')
                    highlight_tag['w:val'] = highlight_color
                    r.find('w:rPr').append(highlight_tag)

    return str(parsed).encode('utf-8')


def highlight_text(highlight_color, text, replacements):

    highlights = [repl[:2] for repl in replacements if repl[2] == 'highlight']
    if not highlights:
        return text

    text = contentsdecode(text)
    parsed = BeautifulSoup(text, 'xml')

    def _process_par(par):
        if not par.find('w:r'):
            return

        phrases = []
        for i in range(len(highlights)):
            phrase, pd_type = highlights[i]
            if pd_type == 'rgx':
                compiled = re.compile(phrase)
                found = compiled.findall(par.text)
                for phrase in found:
                    phrases.append(phrase)
            elif phrase in par.text:
                phrases.append(phrase)

        # Remove inclusive phrases
        clean_phrases = []
        for i in range(len(phrases)):
            if not any(phrases[i] in phrase
                       for phrase in phrases[:i] + phrases[i + 1:]):
                clean_phrases.append(phrases[i])

        clean_run = copy(par.find('w:r'))
        while clean_run.find('w:t'):
            clean_run.find('w:t').decompose()

        runs = [(par.text, 'regular')]
        while par.find('w:r'):
            par.find('w:r').decompose()

        for phrase in phrases:
            new_runs = []
            for text, t in runs:
                if t == 'highlight' or phrase not in text:
                    new_runs.append((text, t))
                    continue

                text_before = text[:text.find(phrase)]
                text_after = text[text.rfind(phrase) + len(phrase):]
                if text_before:
                    new_runs.append((text_before, t))
                new_runs.append((phrase, 'highlight'))
                if text_after:
                    new_runs.append((text_after, t))

            runs = new_runs

        for text, t in runs:
            new_run = copy(clean_run)
            t_tag = parsed.new_tag('w:t')
            t_tag.string = text
            new_run.append(t_tag)

            if t == 'highlight':
                highlight_tag = parsed.new_tag('w:highlight')
                highlight_tag['w:val'] = highlight_color
                if not new_run.find('w:rPr'):
                    rpr = parsed.new_tag('w:rPr')
                    new_run.find('w:t').insert_before(rpr)
                new_run.find('w:rPr').append(highlight_tag)

            par.append(new_run)

    for par in parsed.find_all('w:p'):
        _process_par(par)

    return str(parsed).encode('utf-8')


def obfuscate_document(instance, sents):
    initial_docx = instance.content_file
    result_docx = BytesIO()
    user = instance.source_file.batch.owner
    pd_types = user.profile.personal_data_types
    obf_str = instance.source_file.batch.owner.profile.obfuscate_string
    highlight_color = instance.source_file.batch.owner.profile.highlight_color

    replacements = [
        (pd.text, 'text', pd_types[pd.type][1]) for pd in PersonalData.objects.filter(
            document=instance, selected=True)
    ]
    replacements.extend(
        [(pd.text, 'rgx' if pd.is_rgx else 'text', pd_types[pd.type][1])
         for pd in CustomPersonalData.objects.filter(user=user, selected=True)]
    )
    replacements.sort(key=lambda x: len(x[0]), reverse=True)

    with zipfile.ZipFile(initial_docx, mode='r') as zin, \
            zipfile.ZipFile(result_docx, mode='w',
                            compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename == 'word/document.xml':
                data = obfuscate_sents(obf_str, highlight_color, data, sents)
                data = highlight_text(highlight_color, data, replacements)

            if item.filename in DOCX_TEXT_RELS_FILES:
                data = obfuscate_text(obf_str, data, replacements)

            zout.writestr(item, data)
    result_docx.seek(0)

    return result_docx

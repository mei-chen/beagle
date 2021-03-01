DOCUMENT_TYPES = ['EULA', 'MASTER_SERVICES', 'SERVICES_AGREEMENT', 'TERMS_AND_CONDITIONS',
                  'TERMS_OF_SERVICE', 'USER_AGREEMENT']
DOCUMENT_TYPE_INDICATORS_GRAMMAR = """

EULA:
    {<(End|END|end)\-(User|USER|user).*__.*> <.+__POS>? <(License|LICENSE|license)__.*>? <(Agreement|AGREEMENT|agreement)__.*>}
    {<(End|END|end)__.*> <(User|USER|user).*__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<(End|END|end)\-(User|USER|user).*__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<(End|END|end)__.*> <(User|USER|user).*__.*> <.+__POS>? <(License|LICENSE|license)__.*>? <(Agreement|AGREEMENT|agreement)__.*>}
    {<(End|END|end)\-(User|USER|user).*__.*> <.+__POS>? <(Software|SOFTWARE|software)__.*>? <(Agreement|AGREEMENT|agreement)__.*>}
    {<(End|END|end)__.*> <(User|USER|user).*__.*> <.+__POS>? <(Software|SOFTWARE|software)__.*>? <(Agreement|AGREEMENT|agreement)__.*>}
    {<(License|LICENSE|license)__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<\"?EULA\"?__.*>}
    {<[A-Z].+__.*> <(Customer|CUSTOMER|customer)__.*> <(Agreement|AGREEMENT|agreement)__.*>}

MASTER_SERVICES:
    {<(Master|MASTER|master)__.*>? <(Service|SERVICE|service)(s|S)?__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<(Master|MASTER|master)__.*>? <(Deliverable|DELIVERABLE|deliverable)(s|S)?__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<\"?MSA\"?__.*>}

SERVICES_AGREEMENT:
    {<(Service|SERVICE|service)__.*> <(Level|LEVEL|level)__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<(Professional|PROFESSIONAL|professional)__.*> <(Service|SERVICE|service)__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<\"?SLA\"?__.*>}
    {<(License|LICENSE|license)__.*> <.*>? <(Service|SERVICE|service)__.*> <(Agreement|AGREEMENT|agreement)__.*>}

TERMS_AND_CONDITIONS:
    {<(Terms|TERMS|terms)__.*> <(And|AND|and|&)__.*> <(Conditions|CONDITIONS|conditions)__.*>}
    {<(Terms|TERMS|terms)__.*> <(Of|OF|of)__.*> <(Use|USE|use)__.*>}
    # Terms of use
    {<TOU__.*>}

TERMS_OF_SERVICE:
    {<(Terms|TERMS|terms)__.*> <(Of|OF|of)__.*> <(Service|SERVICE|service)(s|S)?__.*>}
    {<(Terms|TERMS|terms)__.*> <(Through|THROUGH|through)__.*> <(Use|USE|use)__.*>}
    {<\"?T(O|o)S\"?__.*>}

USER_AGREEMENT:
    {<(User|USER|user)__.*> <(Agreement|AGREEMENT|agreement)__.*>}
"""

MENTION_TYPES = ['PRONOUN_MENTION', 'COMPANY_MENTION', 'ENTITY_MENTION']
MENTIONS_GRAMMAR = """
PRONOUN_MENTION:
    {<.*__PRP\$?>}
    {<(We|Our|Us)__.*>}

ENTITY_MENTION:
    {<.*__DT><(Individual|INDIVIDUAL|individual)__.*>}
    {<.*__DT><(Single|SINGLE|single)__.*>?<(Entity|ENTITY|entity)__.*>}
    {<(.*__DT|other__.*)>?<(Legal|LEGAL|legal)__.*>?<(Entity|ENTITY|entity)__.*>}
    {<.*__DT>?<(Licenser|LICENSER|licenser)__NN.*>}
    {<.*__DT>?<(Licensor|LICENSOR|licensor)__NN.*>}
    {<.*__DT>?<(Licensee|LICENSEE|licensee)__NN.*>}
    {<(a|A)__.*><(Single|SINGLE|single)__.*><(End|END|end)__.*><(User|USER|user)__.*>}
    {<(End|END|end)__.*><(User|USER|user)__.*>}
    {<(End|END|end).(User|USER|user)__.*>}
    {<(User|USER|user)__.*>}
    {<(Users|USERS|users)__.*>}
    {<(a|A)__.*><(Single|SINGLE|single)__.*><(End|END| end).(User|USER|user)__.*>}

    # Strangely formatted strings
    {<[a-z]+[A-Z]+[a-z]+__.*>+}
    {<[0-9]+[a-zA-Z]+[a-zA-Z0-9]+__.*>+}

COMPANY_MENTION:
    {<.*__(CD|NN|NNP|NNS|NNPS)>?<(Solutions|SOLUTIONS|solutions)__.+><(Inc|INC|inc|Inc\.|INC\.|inc\.)__.*>}
    {<.+__NNP.*>+<,__.*>?<(Inc|INC|inc|Inc\.|INC\.|inc\.)__.*>}
    {<.+__NN.*><,__.*>?<(Inc|INC|inc|Inc\.|INC\.|inc\.)__.*>}
    {<.+__NNP.*>+<,__.*>?<(Llc|LLC|llc|Llc\.|LLC\.|llc\.)__.*>}
    {<.+__NN.*><,__.*>?<(Llc|LLC|llc|Llc\.|LLC\.|llc\.)__.*>}
    {<.+__NNP.*>+<,__.*>?<(Ltd|LTD|ltd|Ltd\.|LTD\.|ltd\.)__.*>}
    {<.+__NN.*><,__.*>?<(Ltd|LTD|ltd|Ltd\.|LTD\.|ltd\.)__.*>}
    {<.+__NN.*><,__.*>?<(SA|SA\.|S\.A\.)__.*>}
    {<.+__(NNP.*|CD)>*<(U\.?G\.?)__.*>}
    {<.+__NNP.*><.*__.*>?<(GmbH\.?)__.*>}
    {<.+__NNP.*><ApS__.*>}
    {<"__.*><.+__NN.*><,__.*>?<"__.*>}
    {<.+__NNP.*> <UK__N.*> <(Limited|LIMITED|limited)__.*>}
    {<.+__NNP.*> <Company__.*> <(Limited|LIMITED|limited)__.*>}
    {<.+__NNP.*> <(Software|SOFTWARE|software)__.*>}
    {<.+__NNP.*> <(Technologies|TECHNOLOGIES|technologies)__.*>}


MENTION:
    {<PRONOUN_MENTION|COMPANY_MENTION|ENTITY_MENTION>}

MENTION_APPOSITION:
    {<MENTION><.*>?<(Either|EITHER|either)__.*><MENTION><(Or|OR|or)__.*><MENTION>}
    {<MENTION><,__.*>?<\(__.*>?<(Referred|REFERRED|referred)__.*><(To|TO|to)__.*><(Herein|HEREIN|herein)__.*>?<(As|AS|as)__.*>(<\"__.*>?<MENTION><\"__.*>?)+(<or__.*><\"__.*>?<MENTION><\"__.*>?)?<\)__.*>?}
    {<(Referred|REFERRED|referred)__.*><(To|TO|to)__.*><(Herein|HEREIN|herein)__.*>?<(As|AS|as)__.*>(<\"__.*>?<MENTION><\"__.*>?)+(<or__.*><\"__.*>?<MENTION><\"__.*>?)?}
    {<MENTION><,__.*>?<\(__.*>?<(Herein|HEREIN|herein|Hereafter|HEREAFTER|hereafter)__.*><(As|AS|as)__.*>?<\"__.*>?<MENTION><\"__.*>?<\)__.*>?}

    {<\"__.*><MENTION><\"__.*><,__.*><\"__.*><MENTION><\"__.*>(<(,|or)__.*><\"__.*><MENTION><\"__.*>)*}
    {<MENTION><\(__.+><MENTION><\)__.+>}

MENTION_LINK:
    {<(Between|BETWEEN|between)__.+><MENTION|MENTION_APPOSITION><.*__.*>*<(And|AND|and|,)__.*><MENTION|MENTION_APPOSITION>}

MENTION_INDICATOR:
    {<MENTION|MENTION_APPOSITION|MENTION_LINK>}
"""

REFERENCES_TYPES = ['REFERENCE', 'STANDARD']
EXTERNAL_REFERENCES_GRAMMAR = """
REFERENCE:
    {<(Follow|FOLLOW|follow)__.*><[A-Z].*__.*>+<(Policy|POLICY|policy|Policies|POLICIES|policies|Terms|TERMS|terms|Procedure|PROCEDURE|procedure)__.*>}
    {<(Adhere|ADHERE|adhere)__.*><(To|TO|to)__.*><[A-Z].*__.*>+<(Policy|POLICY|policy|Policies|POLICIES|policies|Terms|TERMS|terms|Procedure|PROCEDURE|procedure)__.*>}
    {<(Conform|CONFORM|conform)__.*><(To|TO|to)__.*><[A-Z].*__.*>+<(Standards?|STANDARDS?|standards?)__.*>}
    {<(Be|BE|be)__.*><(Bound|BOUND|bound)__.*><(By|BY|by)__.*><[A-Z].*__.*>+<(Policy|POLICY|policy|Policies|POLICIES|policies|Terms|TERMS|terms|Procedure|PROCEDURE|procedure)__.*> <(And|AND|and)__.*> <(Conditions?|CONDITIONS?|conditions?)__.*> <.*>* <(THIS|This|this)__.*> <(Agreement|AGREEMENT|agreement)__.*>}
    {<(Be|BE|be)__.*><(Bound|BOUND|bound)__.*><(By|BY|by)__.*><[A-Z].*__.*>+<(Policy|POLICY|policy|Policies|POLICIES|policies|Terms|TERMS|terms|Procedure|PROCEDURE|procedure)__.*>}
    {<.*>* <(On|ON|on)__.*> <(This|THIS|this|That|THAT|that|The|THE|the)__.*> <(Webpage|WEBPAGE|webpage)__.*> <.*>*}
    {<.*>* <(On|ON|on)__.*> <(This|THIS|this|That|THAT|that|The|THE|the)__.*> <(Website|WEBSITE|website)__.*> <.*>*}

STANDARD:
    {<ITIL2\.0__.*>}
    {<ITIL__.*><2\.0__.*>}
    {<SCORM2\.0__.*>}
    {<SCORM__.*><2\.0__.*>}
    {<ISO27001__.*>}
    {<ISO__.*><27001__.*>}
    {<ISO(/IEC)?__.*><(IS|TR)?[0-9]+(\-[0-9]+)?__.*>}
    {<ISO[0-9]+(\-[0-9]+)?__.*>}
    {<EU__.*><(Directive|DIRECTIVE)__.*><[A-Z0-9/\.\-\_]+>}
    {<(Digital|DIGITAL|digital)__.*><(Millennium|MILLENNIUM|millennium)__.*><(Copyright|COPYRIGHT|copyright)__.*><(Act|ACT|act)__.*>}
    {<DMCA__.*>}
    {<PEGI__.*>}
    {<DFARS__.*>}
    {<DCAA__.*>}
    {<USK__.*>}
    {<ACB__.*>}
    # From Vidyard agreement
    {<SOCAN__.*>}
    {<ASCAP__.*>}
    {<BMI__.*>}
    {<SESAC__.*>}
    {<USPAP__.*>}
    # From Axonify agreement
    {<(Can-Spam|CAN-SPAM|can-spam)__.*>}
    {<(Can|CAN|can)__.*> <-__.*>? <(Spam|SPAM|spam)__.*>}
    {<(Pipeda|PIPEDA|pipeda)__.*>}
    # Material safety data sheet
    {<MSDS__.*>}
    #Digital Rights Management (DRM)
    {<(Anti|ANTI|anti)__.*> <-__.*>? <(Spam(ming)?|SPAM(MING)?|spam(ming)?)__.*> <(Polic(y|ies)|POLIC(Y|IES)|polic(y|ies)|Laws?|LAWS?|laws?)__.*>}
    {<(Anti-spam(ming)?|Anti-Spam(ming)?|ANTI-SPAM(MING)?|anti-spam(ming)?)__.*> <(Polic(y|ies)|POLIC(Y|IES)|polic(y|ies)|Laws?|LAWS?|laws?)__.*>}
"""

LIABILITIES_TYPES = ['NO_LIABILITY', 'PARTIAL_LIABILITY', 'ABSOLUTE_LIABILITY']
LIABILITIES_GRAMMAR = """
MPARTY:
{% for p in party_mentions %}
    { {{ p|safe }} }
{% endfor %}

LIABLE_KW:
    {<(Liable|LIABLE|liable|Responsible|RESPONSIBLE|responsible)__.*> (<(Or|OR|or|And|AND|and)__.*> <(Liable|LIABLE|liable|Responsible|RESPONSIBLE|responsible)__.*>)?}

{% if both %}
BOTH_PARTIES:
    {<(A|a)__.*> <(Party|PARTY|party)__.*>}
    {<(Either|EITHER|either)__.*> <(Party|PARTY|party)__.*>}
    {<(Each|EACH|each)__.*> <(Party|PARTY|party)__.*>}
    {<(Both|BOTH|both)__.*> <(Parties|PARTIES|parties)__.*>}
    {<MPARTY> <(Or|OR|or)__.*> <MPARTY>}
    {<MPARTY> <(And|AND|and)__.*> <MPARTY>}
    {<(The|THE|the)__.*> <(Other|OTHER|other)__.*> <(Party|PARTY|party)__.*>}
{% endif %}

NO_LIABILITY:
{% if both %}
    {<BOTH_PARTIES> <(Shall|SHALL|shall)__.*> <(Not|NOT|not)__.*> <(Be|BE|be)__.*> <LIABLE_KW>}
    {<(Neither|NEITHER|neither)__.*> <(Party|PARTY|party)__.*> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Be|BE|be)__.*> <LIABLE_KW>}
    {<(Neither|NEITHER|neither)__.*> <(Party|PARTY|party)__.*> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Have|HAVE|have)__.*> <(Any|ANY|any)__.*> <(Liability|LIABILITY|liability)__.*>}
    {<(Neither|NEITHER|neither)__.*> <(Party|PARTY|party)__.*> <.*__POS> <(Liability|LIABILITY|liability)__.*>}
    {<(Neither|NEITHER|neither)__.*> <(Party|PARTY|party)__.*> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Have|HAVE|have)__.*> <(Liability|LIABILITY|liability)__.*>}
    {<(Neither|NEITHER|neither)__.*> <.*>* <(Parties|PARTIES|parties)__.*> <.*>* <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Be|BE|be)__.*> <LIABLE_KW>}
    {<BOTH_PARTIES> <.*>* <(Are|ARE|are)__.*> <(Not|NOT|not)__.*> <LIABLE_KW>}
{% else %}
    {<MPARTY> <(Nor|NOR|nor)__.*> <.*>* <(Shall|SHALL|shall)__.*> <(Be|BE|be)__.*> <LIABLE_KW> <.*>*}
    {<(Nor|NOR|nor)__.*> <MPARTY> <(Shall|SHALL|shall)__.*> <(Be|BE|be)__.*> <LIABLE_KW> <.*>*}
    {<(Agree|AGREE|agree)__.*> <(That|THAT|that)__.*> <MPARTY> <(Shall|SHALL|shall)__.*><(Not|NOT|not)__.*> <(BE|Be|be)__.*> <LIABLE_KW><.*>*}
    {<MPARTY><(Is|IS|is|Are|ARE|are)__.*><(Not|NOT|not)__.*><LIABLE_KW><.*>*}
    {<MPARTY> <(Does|DOES|does)__.*> <(Not|NOT|not)__.*> <(Warrant|WARRANT|warrant)__.*><.*>*}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Event|EVENT|event)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*><MPARTY><.*>*<(Any|ANY|any)__.*><.*>*<(Liability|LIABILITY|liability)__.*>}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Event|EVENT|event)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*><MPARTY><.*>*<(Be|BE|be)__.*><LIABLE_KW>}
    {<MPARTY> <(Has|HAS|has|Have|HAVE|have)__.*> <.*>* <(No|NO|no)__.*> <(Liability|LIABILITY|liability|Obligations?|OBLIGATIONS?|obligations?)__.*><.*>*}
    {<MPARTY> <(Shall|SHALL|shall)__.*> <(Have|HAVE|have)__.*> <.*>* <(No|NO|no)__.*> <(Liability|LIABILITY|liability|Obligations?|OBLIGATIONS?|obligations?)__.*> <.*>*}
    {<(Under|UNDER|under)__.*> <(No|NO|no)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*> <MPARTY> <.*>* <(Be|BE|be)__.*><LIABLE_KW>}
    {<MPARTY> <.*>* <(Is|IS|is)__.*> <(Not|NOT|not)__.*> <(Undertaking|UNDERTAKING|undertaking)__.*> <(Any|ANY|any)__.*> <(Obligations|OBLIGATIONS|obligation)__.*> <(Or|OR|or)__.*><(Liablility|LIABILITY|liability)__.*><.*>*}
    {<MPARTY> <.*>* <(Assumes?|ASSUMES?|assumes?)__.*> <(No|NO|no)__.*> (<(Responsibility|RESPONSIBILITY|responsibility)__.*> <(Or|OR|or)__.*>)? <(Liability|LIABILITY|liability)__.*>}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Way|WAY|way)__.*><(Will|WILL|will)__.*> <MPARTY> <.*>* <(Be|be|BE)__.*><LIABLE_KW><.*>*}
    {<MPARTY> <(IS|Is|is|BE|Be|be|ARE|Are|are)__.*> <(NOT|Not|not)__.*><LIABLE_KW><(For|FOR|for)__.*><.*>}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><LIABLE_KW><.*>*}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Held|HELD|held)__.*><LIABLE_KW><.*>}
    {<MPARTY><(Shall|SHALL|shall)__.*><(Not|NOT|not)__.*><,__.*><(Under|UNDER|under)__.*> <(Any|ANY|any)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*> <,__.*><(Be|BE|be)__.*><LIABLE_KW><.*>*}

    #{<MPARTY><.*>*<(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><LIABLE_KW><.*>*}
    #{<MPARTY><.*>*<(Shall|SHALL|shall)__.*><(Not|NOT|not)__.*><,__.*><(Under|UNDER|under)__.*> <(Any|ANY|any)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*> <,__.*><(Be|BE|be)__.*><LIABLE_KW><.*>*}
    #{<MPARTY><.*>*<(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Held|HELD|held)__.*><LIABLE_KW><.*>}
    
    # You will defend Us against any claim, demand, suit or proceeding made or brought against Us ...
    {<(Shall|SHALL|shall|Will|WILL|will)__.*> <(Defend|DEFEND|defend)__.*> <MPARTY> <(Against|AGAINST|against|From|FROM|from)__.*> <(Any|ANY|any)__.*>}

    {<(Hold|HOLD|hold)__.*> <MPARTY> <.*>* <(Harmless|HARMLESS|harmless)__.*> <(From|FROM|from)__.*>}
    {<(Hold|HOLD|hold)__.*> <(Harmless|HARMLESS|harmless)__.*> <.*>* <MPARTY>}

    # Corfo shall bear no liability of any kind for any loss that may occur to third parties.
    {<MPARTY><(Shall|SHALL|shall)__.*><(Bear|bear|BEAR)__.*><(No|NO|no)__.*><(Liability|LIABILITY|liability)__.*><.*>}

{% endif %}

PARTIAL_LIABILITY:
{% if both %}
    {<BOTH_PARTIES><(Liablility|LIABILITY|liability)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<BOTH_PARTIES><(Shall|SHALL|shall)__.*><(Only|ONLY|only)__.*><(Be|BE|be)__.*><LIABLE_KW>}
    {<BOTH_PARTIES><(Total|TOTAL|total)__.*><(Liablility|LIABILITY|liability)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<BOTH_PARTIES><(Total|TOTAL|total)__.*><(Liablility|LIABILITY|liability)__.*><.*>*<(Shall|SHALL|shall)__.*><(Not|not|NOT)__.*><(Exceed|EXCEED|exceed)__.*><.*>*<.*__N.*>}
{% else %}
    {<MPARTY> <.*>? <.*>? <(Aggregate|AGGREGATE|aggregate)__.*> <(Liability|LIABILITY|liability)__.*>}
    {<MPARTY><(Liablility|LIABILITY|liability)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<MPARTY><(Shall|SHALL|shall)__.*><(Only|ONLY|only)__.*><(Be|BE|be)__.*><LIABLE_KW>}
    {<MPARTY><(Total|TOTAL|total)__.*><(Liablility|LIABILITY|liability)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<MPARTY><(Total|TOTAL|total)__.*><(Liablility|LIABILITY|liability)__.*><.*>*<(Shall|SHALL|shall)__.*><(Not|not|NOT)__.*><(Exceed|EXCEED|exceed)__.*><.*>*<.*__N.*>}
{% endif %}

ABSOLUTE_LIABILITY:
{% if both %}
    {<BOTH_PARTIES><(Shall|SHALL|shall|Will|WILL|will)__.*><(Be|BE|be)__.*><LIABLE_KW> <.*>*}
    {<BOTH_PARTIES><.*>*<(Shall|SHALL|shall|Will|WILL|will)__.*><(Be|BE|be)__.*><LIABLE_KW> <.*>*}
    {<BOTH_PARTIES> <.*>* <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Indemnify|INDEMNIFY|indemnify)__.*>}
{% else %}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will)__.*><(Be|BE|be)__.*><LIABLE_KW> <.*>*}
    {<MPARTY><.*>*<(Shall|SHALL|shall|Will|WILL|will|May|MAY|may)__.*><(Be|BE|be)__.*><LIABLE_KW> <.*>*}
    {<MPARTY> <.*> <(Fully|FULLY|fully)__.*> <LIABLE_KW>}
    {<MPARTY> <.*> <(Completely|COMPLETELY|completely|Absolutely|ABSOLUTELY|ABSOLUTELY|Fully|FULLY|fully|Solely|SOLELY|solely)__.*> <LIABLE_KW>}
    {<MPARTY> <.*> <(Complete|COMPLETE|complete|Absolute|ABSOLUTE|ABSOLUTE|Full|FULL|full|Sole|SOLE|sole)__.*> <(Liablility|LIABILITY|liability)__.*>}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will)__.*><(Indemnify|INDEMNIFY|indemnify)__.*><.*>*}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will)__.*><(Defend|DEFEND|defend)__.*><.*>*}
    {<MPARTY><(Also|ALSO|also)__.*>*<(Agrees?|AGREES?|agrees?)__.*><(To|TO|to)__.*> <.*>* <(Indemnify|INDEMNIFY|indemnify)__.*> <.*>*}
    {<MPARTY><(Agrees?|AGREES?|agrees?)__.*><(At|AT|at)__.*><(All|ALL|all)__.*> <(Times|TIMES|times)__.*> <(To|TO|to)__.*><(Indemnify|INDEMNIFY|indemnify)__.*> <.*>*}
    {<MPARTY> <(Assumes?|ASSUMES?|assumes?)__.*> <(The|THE|the)__.*> <(Entire|ENTIRE|entire)__.*>? (<(Responsibility|RESPONSIBILITY|responsibility)__.*> <(And|AND|and)__.*>)? <(Liability|LIABILITY|liability)__.*>}

    {<MPARTY> <(Shall|SHALL|shall|Will|WILL|will)__.*> (<.*>+ <.*__CC>)? <(Hold|HOLD|hold)__.*> <.*> <(Harmless|HARMLESS|harmless)__.*> <(From|FROM|from|Against|AGAINST|against)__.*> (<(And|AND|and)__.*> <(Against|AGAINST|against)__.*>)? <(All|ALL|all)__.*> <(Liabilities|LIABILITIES|liabilities)__.*>}

    {<MPARTY> <.*> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Maintain|MAINTAIN|maintain)__.*> <(Liablility|LIABILITY|liability)__.*>}
{% endif %}

"""


RESPONSIBILITY_TYPES = ['NO_RESPONSIBILITY',
                        'PARTIAL_RESPONSIBILITY',
                        'ABSOLUTE_RESPONSIBILITY',
                        'CONDITIONAL_ABSOLUTE_RESPONSIBILITY']
RESPONSIBILITY_GRAMMAR = """
MPARTY:
{% for p in party_mentions %}
    { {{ p|safe }} }
{% endfor %}

{% if both %}
BOTH_PARTIES:
    {<(A|a)__.*> <(Party|PARTY|party)__.*>}
    {<(Either|EITHER|either)__.*> <(Party|PARTY|party)__.*>}
    {<(Each|EACH|each)__.*> <(Party|PARTY|party)__.*>}
    {<(Both|BOTH|both)__.*> <(Parties|PARTIES|parties)__.*>}
    {<MPARTY> <(Or|OR|or|Nor|NOR|nor)__.*> <MPARTY>}
    {<MPARTY> <(And|AND|and)__.*> <MPARTY>}
    {<(The|THE|the)__.*> <(Other|OTHER|other)__.*> <(Party|PARTY|party)__.*>}
{% endif %}

NO_RESPONSIBILITY:
{% if both %}
    {<(Neither|NEITHER|neither)__.*> <(Party|PARTY|party)__.*> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Be|BE|be)__.*> <(Responsible|RESPONSIBLE|responsible)__.*>}
{% else %}
    {<(Agree|AGREE|agree)__.*> <(That|THAT|that)__.*> <MPARTY> <(Shall|SHALL|shall|Will|WILL|will)__.*><(Not|NOT|not)__.*> <(BE|Be|be)__.*> <(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY><(Is|IS|is|Are|ARE|are)__.*><(Not|NOT|not)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Event|EVENT|event)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*><MPARTY><.*>*<(Any|ANY|any)__.*><.*>*<(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Event|EVENT|event)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*><MPARTY><.*>*<(Be|BE|be)__.*><(Responibile|RESPONIBILE|responibile)__.*><.*>*}
    {<MPARTY> <(Is|IS|is|Are|ARE|are)__.*> <.*>* <(Not|NOT|not)__.*> <(Responsible|RESPONSIBLE|responsible)__.*> <.*>* <(Whatsoever|WHATSOEVER|whatsoever)__.*>}
    {<MPARTY> <(Is|IS|is|Are|ARE|are)__.*> <.*>* <(Not|NOT|not)__.*> <(Responsible|RESPONSIBLE|responsible)__.*><(For|FOR|for)__.*><.*>*}
    {<MPARTY> <(Is|IS|is|Are|ARE|are)__.*> <.*>* <(Not|NOT|not)__.*> <(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY> <(Has|HAS|has|Have|HAVE|have)__.*> <.*>* <(No|NO|no)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*><.*>*}
    {<(Under|UNDER|under)__.*> <(No|NO|no)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*><(Shall|SHALL|shall|Will|WILL|will)__.*> <MPARTY> <(Be|BE|be)__.*><(Responsibile|RESPONSIBILE|responsibile)__.*><.*>*}
    {<MPARTY> <.*>* <(Is|IS|is)__.*> <(Not|NOT|not)__.*> <(Undertaking|UNDERTAKING|undertaking)__.*> <(Any|ANY|any)__.*> <(Obligations?|OBLIGATIONS?|obligations?)__.*> <(Or|OR|or)__.*><(Responsibility|RESPONSIBILITY|responsibility)__.*><.*>*}
    {<MPARTY> <(Is|IS|is)__.*> <(Not|NOT|not)__.*> <(Under|UNDER|under)__.*> <(Any|ANY|any)__.*> <(Obligations?|OBLIGATIONS?|obligations?)__.*> <.*>*}
    {<MPARTY> <(Is|IS|is)__.*> <(Under|UNDER|under)__.*> <(No|NO|no)__.*> <(Obligations?|OBLIGATIONS?|obligations?)__.*> <.*>*}
    {<MPARTY> <.*>* <(Assumes|ASSUMES|assumes)__.*> <(No|NO|no)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*><.*>*}
    {<MPARTY> <(Takes|TAKES|takes)__.*> <(No|NO|no)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*><.*>*}
    {<(In|IN|in)__.*><(No|NO|no)__.*><(Way|WAY|way)__.*><(Will|WILL|will)__.*> <MPARTY> <.*>* <(Be|be|BE)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY> <(IS|Is|is|BE|Be|be|ARE|Are|are)__.*> <(NOT|Not|not)__.*><(Responsible|RESPONSIBLE|responsible)__.*><(For|FOR|for)__.*><.*>}
    {<MPARTY> <(IS|Is|is|BE|Be|be|ARE|Are|are)__.*> <(NOT|Not|not)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*> }
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY><.*>*<(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY><(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Held|HELD|held)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>}
    {<MPARTY><.*>*<(Shall|SHALL|shall|Will|WILL|will|Can|CAN|can)__.*><(Not|NOT|not)__.*><(Be|BE|be)__.*><(Held|HELD|held)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>}
    {<MPARTY><(Shall|SHALL|shall)__.*><(Not|NOT|not)__.*><,__.*><(Under|UNDER|under)__.*> <(Any|ANY|any)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*> <,__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<MPARTY><.*>*<(Shall|SHALL|shall)__.*><(Not|NOT|not)__.*><,__.*><(Under|UNDER|under)__.*> <(Any|ANY|any)__.*> <(Circumstances|CIRCUMSTANCES|circumstances)__.*> <,__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
{% endif %}

PARTIAL_RESPONSIBILITY:
{% if both %}
    {<BOTH_PARTIES> <.*__POS>? <(Responsibility|RESPONSIBILITY|responsibility)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
{% else %}
    {<MPARTY><(Responsibility|RESPONSIBILITY|responsibility)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<MPARTY><(Shall|SHALL|shall)__.*><(Only|ONLY|only)__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY><(Total|TOTAL|total)__.*><(Responsibility|RESPONSIBILITY|responsibility)__.*><(Is|IS|is)__.*><(Limited|LIMITED|limited)__.*><(To|TO|to)__.*>}
    {<MPARTY><(Total|TOTAL|total)__.*><(Responsibility|RESPONSIBILITY|responsibility)__.*><.*>*<(Shall|SHALL|shall)__.*><(Not|not|NOT)__.*><(Exceed|EXCEED|exceed)__.*><.*>*<.*__N.*>}
{% endif %}

ABSOLUTE_RESPONSIBILITY:
{% if both %}
    {<BOTH_PARTIES><.*>*<(Shall|SHALL|shall|Will|WILL|will)__.*><(Be|BE|be)__.*><(Responsible|RESPONSIBLE|responsible)__.*><.*>*}
    {<(Neither|NEITHER|neither)__.*> <BOTH_PARTIES> <(Shall|SHALL|shall|Will|WILL|will)__.*> <.*__V.*>}
{% else %}
    {<MPARTY> <(Acknowledge|ACKNOWLEDGE|acknowledge)__.*> <(That|THAT|that)__.*>}
    {<MPARTY> <(Will|WILL|will|May|MAY|may)__.*> <(Not|NOT|not)__.*> <(Sell|SELL|sell|Assign|ASSIGN|assign|Transfer|TRANSFER|transfer|Share|SHARE|share)__.*>}
    {<MPARTY> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Maintain|MAINTAIN|maintain)__.*> <.*>*}
    {<MPARTY> <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Control|CONTROL|control)__.*> <.*>*}
    {<MPARTY> <(Agree|AGREE|agree)__.*> <(That|THAT|that)__.*> <(Shall|SHALL|shall|Will|WILL|will)__.*><(Not|NOT|not)__.*> <.*>*}
    {<MPARTY> <(Agree|AGREE|agree)__.*> <(That|THAT|that)__.*> <MPARTY> <(Will|WILL|will)__.*><.*__V.*>}
    # Party (shall/will/must) <*.> conform/conforms <*.> to PartyB's <*.> policy/policies <*.>
    {<MPARTY> <(Shall|SHALL|shall|Will|WILL|will|Must|MUST|must)___.*> <.*>* <(Conforms?|CONFORMS?|conforms?)__.*> <.*>* <(To|TO|to)__.*> <.*>* <(Polic(y|ies)|POLIC(Y|IES)|polic(y|ies))__.*> <.*>*}
    {<(Is|IS|is)___.*> <(The|THE|the)__.*> <(Sole|SOLE|sole)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*> <(Of|OF|of)__.*> <MPARTY> <.*>*}
    {<MPARTY> <(Is|IS|is|ARE|Are|are)__.*> <.*>* <(Solely|SOLELY|solely)__.*>? <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <(Is|IS|is)___.*> <(Solely|SOLELY|solely)__.*> <(Responsible|RESPONSIBLE|responsible)__.*> <(For|FOR|for)__.*>}
    {<.*>* <(Shall|SHALL|shall|Will|WILL|will)__.*> <(BE|Be|be)__.*> <MPARTY> <.*__POS>? <(Sole|SOLE|sole)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<.*>* <(IS|Is|is|ARE|Are|are)__.*> <MPARTY> <.*__POS>? <(Sole|SOLE|sole)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<MPARTY> <.*>* <(Shall|SHALL|shall|Will|WILL|will)__.*> <(Be|BE|be)__.*> <(Personally|PERSONALLY|personally)__.*>? <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <.*> <(Fully|FULLY|fully)__.*> <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <.*>+ <(Solely|SOLELY|solely)__.*> <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <.*> <(Completely|COMPLETELY|completely)__.*> <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <.*> <(Absolutely|ABSOLUTELY|ABSOLUTELY)__.*> <(Responsible|RESPONSIBLE|responsible)__.*>}
    {<MPARTY> <.*> <(Full|FULL|full)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<MPARTY> <.*> <(Complete|COMPLETE|complete)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<MPARTY> <.*> <(Absolute|ABSOLUTE|ABSOLUTE)__.*> <(Responsibility|RESPONSIBILITY|responsibility)__.*>}
    {<MPARTY> <(Also|ALSO|also)__.*>? <(Will|WILL|will)__.*> <(Ensure|ENSURE|ensure)__.*> <.*>*}
    {<MPARTY> <(Also|ALSO|also)__.*>? <(Shall|SHALL|shall)__.*> <(Ensure|ENSURE|ensure)__.*> <.*>*}
    {<MPARTY> <(Must|MUST|must)__.*> <(Comply|COMPLY|comply)__.*> <.*>*}
    {<MPARTY> <(Must|MUST|must|Will|WILL|will)__.*> <(Provide|PROVIDE|provide)__.*>}
    # 2 broad rules
    {<MPARTY> <(Shall|SHALL|shall)__.*>}
    {<MPARTY> <(Must|MUST|must|Will|WILL|will)__.*>}
    # Customer's responsibility includes ...
    {<MPARTY> <.*__POS>? <(Responsibilit(y|ies)|RESPONSIBILIT(Y|IES)|responsibilit(y|ies))__.*> <(Includes?|INCLUDES?|includes?)__.*>}
    # responsibility of the Customer includes ...
    {<(Responsibilit(y|ies)|RESPONSIBILIT(Y|IES)|responsibilit(y|ies))__.*> <(Of|OF|of)__.*> <(The|THE|the)__.*>? <MPARTY> <(Includes?|INCLUDES?|includes?)__.*>}
    {<MPARTY> <(Is|IS|is)__.*> <(Personally|PERSONALLY|personally|Solely|SOLELY|solely|Fully|FULLY|fully)__.*>? <(Responsible|RESPONSIBLE|responsible)__.*> <(To|TO|to)__.*>}

    {<MPARTY> <(Is|IS|is)__.*> <(Agreeable|AGREEABLE|agreeable)__.*> <(To|TO|to)__.*> <(Providing|PROVIDING|providing)__.*> <.*__.*>? <(Services|SERVICES|services)__.*>}
    {<MPARTY> <.*>* <(Agrees?|AGREES?|agrees?)__.*> <(To|TO|to)__.*> <(Provide|PROVIDE|provide)__.*> }
    {<MPARTY> <(Covenants?|COVENANTS?|covenants?)__.*>}
    {<MPARTY> <(Promises?|PROMISES?|promises?)__.*>}
{% endif %}


{% if not both %}
CONDITIONAL_ABSOLUTE_RESPONSIBILITY:
    {<(If|IF|if)__.*> <MPARTY> <.*>* <MPARTY> <(Must|MUST|must|Shall|SHALL|shall)__.*>}
    {<(If|IF|if)__.*> <.*>* <,__.*> <MPARTY> <(Must|MUST|must|Shall|SHALL|shall)__.*>}
    {<(If|IF|if)__.*> <.*>* <,__.*> <MPARTY> <(Must|MUST|must|Shall|SHALL|shall)__.*>}
    {<(If|IF|if)__.*> <.*>* <,__.*> <NO_RESPONSIBILITY|PARTIAL_RESPONSIBILITY|ABSOLUTE_RESPONSIBILITY>}
    {<(Then|THEN|then)__.*> <MPARTY> <(Will|WILL|will)__.*> <(Has|HAS|has|Have|HAVE|have)__.*> <(To|TO|to)__.*> <(Pay|PAY|pay)__.*>}
    {<(Then|THEN|then)__.*> <MPARTY> <(Will|WILL|will)__.*> <(Be|BE|be)__.*> <(Required|REQUIRED|required)__.*> <(To|TO|to)__.*> <(Pay|PAY|pay)__.*>}
{% endif %}

"""

TERMINATION_TYPES = ['PARTIAL_TERMINATION',
                     'ABSOLUTE_TERMINATION',
                     'CONDITIONAL_ABSOLUTE_TERMINATION',
                     'CONDITIONAL_PARTIAL_TERMINATION']

TERMINATION_GRAMMAR = """
MPARTY:
{% for p in party_mentions %}
    { {{ p|safe }} }
{% endfor %}

{% if both %}
BOTH_PARTIES:
    {<(A|a)__.*> <(Party|PARTY|party)__.*>}
    {<(The|THE|the)__.*> <.*>? <(Part(y|ies)|PART(Y|IES)|part(y|ies))__.*>}
    {<(Either|EITHER|either)__.*> <(Party|PARTY|party)__.*>}
    {<(Each|EACH|each)__.*> <(Party|PARTY|party)__.*>}
    {<(Both|BOTH|both)__.*> <(Parties|PARTIES|parties)__.*>}
    {<MPARTY> <(Or|OR|or)__.*> <MPARTY>}
    {<MPARTY> <(And|AND|and)__.*> <MPARTY>}
    {<(The|THE|the)__.*> <(Other|OTHER|other)__.*> <(Party|PARTY|party)__.*>}
{% endif %}

TERM_KW:
    {<(Immediately|IMMEDIATELY|immediately)__.*>? <(Suspends?|SUSPENDS?|suspends?)__.*> (<,__,>|<(Or|OR|or)__.*>) <(Terminates?|TERMINATES?|terminates?)__.*>}
    {<(Immediately|IMMEDIATELY|immediately)__.*>? <(Terminates?|TERMINATES?|terminates?)__.*>}
    {<(Immediately|IMMEDIATELY|immediately)__.*>? <(Suspends?|SUSPENDS?|suspends?)__.*>}
    {<(Terminated|TERMINATED|terminated)__.*>}

CONDITIONAL_ABSOLUTE_TERMINATION:
{% if both %}
    {<(If|IF|if)__.*> <BOTH_PARTIES> <.*>* <(Right|RIGHT|right)__.*> <(To|TO|to)__.*> <TERM_KW>}
    {<(If|IF|if)__.*> <.*>* <BOTH_PARTIES> <.*>* <(Right|RIGHT|right)__.*> <(To|TO|to)__.*> <TERM_KW>}
    {<BOTH_PARTIES> <(May|MAY|may)__.*> <TERM_KW> <.*>* <(If|IF|if)__.*>}
    {<(If|IF|if)__.*> <.*>* <BOTH_PARTIES> <(May|MAY|may)__.*> <TERM_KW>}
{% else %}
    {<(If|IF|if)__.*> <MPARTY> <.*>* <(Right|RIGHT|right)__.*> <(To|TO|to)__.*> <TERM_KW>}
    {<MPARTY> <(May|MAY|may)__.*> <TERM_KW> <.*>* <(If|IF|if)__.*>}
    {<MPARTY> <(May|MAY|may)__.*> <TERM_KW> <.*>* <(In|IN|in)__.*> <(The|THE|the)__.*> <(Event|EVENT|event)__.*> <(Of|OF|of)__.*>}
    {<MPARTY> <(May|MAY|may)__.*> <(Only|ONLY|only)__.*> <TERM_KW>}
    {<(If|IF|if)__.*> <.*>* <MPARTY> <(May|MAY|may)__.*> <.*>* <TERM_KW>}
{% endif %}

{% if not both %}
CONDITIONAL_PARTIAL_TERMINATION:
    {<MPARTY> <(May|MAY|may)__.*> <TERM_WK> <(Any|any|ANY)__.*> <(Or|OR|or)__.*> <(All|ALL|all)__.*>}
{% endif %}

ABSOLUTE_TERMINATION:
{% if both %}
    {<BOTH_PARTIES> <(May|MAY|may|Can|CAN|can)__.*> (<,__.*> <.*>* <,__.*>)? <TERM_KW>}
    {<BOTH_PARTIES> <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also)__.*>? <TERM_KW> <(This|THIS|this|The|THE|the)__.*> <.*>* <(At|AT|at)__.*> <(Any|ANY|any)__.*> <(Time|TIME|time)__.*>}
    {<BOTH_PARTIES> <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also)__.*>? <TERM_KW>}

    # either Party wishes to terminate
    {<BOTH_PARTIES> <(Wants?|WANTS?|wants?|Wishes|WISHES|wishes|Wish|WISH|wish)__.*> <(To|TO|to)__.*>? <TERM_KW>}

    {<BOTH_PARTIES> <.*>* <(Written|WRITTEN|written)__.*> <(Notice|NOTICE|notice)__.*> <(Of|OF|of)__.*> <(Termination|TERMINATION|termination)__.*> <.*>*}
    {<(Terminated|TERMINATED|terminated)__.*> <.*>* <BOTH_PARTIES> <.*>* <(Notice|NOTICE|notice)__.*> <.*>*}
    {<(On|ON|on)__.*> <(Termination|TERMINATION|termination)__.*> <.*>* <(Shall|SHALL|shall)__.*> <(Survive|SURVIVE|survive)__.*>}
    {<(This|THIS|this|The|THE|the)__.*> <(Agreement|AGREEMENT|agreement)__.*> <(May|MAY|may|Can|CAN|can)__.*> <(Be|BE|be)__.*> <TERM_KW>}
    {<BOTH_PARTIES> <(Reserves?|RESERVES?|reserves?)__.*> <(The|THE|the)__.*> <(Right|RIGHT|right)__.*> (<,__.*> <.*>* <,__.*>)? <(To|TO|to)__.*> <.*>* <TERM_KW>}
{% else %}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also)__.*>? (<,__.*> <.*>* <,__.*>)? <TERM_KW>}
    {<MPARTY> (<,__.*> <.*>* <,__.*>)? <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also|Not|NOT|not)__.*>? <TERM_KW>}
    {<MPARTY> <'s__.*> <(Rights?|RIGHTS?|rights?)__.*> <(To|TO|to)__.*> <TERM_KW> <(Are|ARE|are)__.*> <(Limited|LIMITED|limited)__.*>}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> (<,__,> <.*>*)? <TERM_KW> (<,__,> <.*>*)? <(Your|YOUR|your)__.*>* <(License|LICENSE|license|Access|ACCESS|access)__.*><.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <TERM_KW> <(This|THIS|this|The|THE|the)__.*> <.*>* <(At|AT|at)__.*> <(Any|ANY|any)__.*> <(Time|TIME|time)__.*><.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <TERM_KW> <(This|THIS|this|The|THE|the)__.*> <.*>* <(If|IF|if)__.*> <.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <(At|AT|at)__.*> <(Any|ANY|any)__.*> <(Time|TIME|time)__.*> <TERM_KW><.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <TERM_KW> <(This|THIS|this|The|THE|the)__.*> <.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <(Then|THEN|then)__.*> <TERM_KW> <(This|THIS|this|The|THE|the)__.*> <.*>*}
    {<MPARTY> <,__.*> <.*>* <,__.*> <(May|MAY|may)__.*> <TERM_KW> <.*> <(License|LICENSE|license)__.*><.*>*}
    {<MPARTY> <(Shall|SHALL|shall)__.*> <(Have|HAVE|have)__.*> <(The|THE|the|a|A)__.*> <(Rights?|RIGHTS?|rights?)__.*><(To|TO|to)__.*> <TERM_KW><.*>*}
    {<(This|THIS|this|The|THE|the)__.*> <.*> <(Will|WILL|will)__.*> <TERM_KW> <(Automatically|AUTOMATICALLY|automatically)__.*> <(If|IF|if)__.*> <MPARTY> <(Fails?|FAILS?|fails?)__.*><.*>*}
    {<(This|THIS|this|The|THE|the)__.*> <.*> <(Will|WILL|will)__.*> <TERM_KW> <(Upon|UPON|upon)__.*> <MPARTY> <.*>* <(Breach|BREACH|breach)__.*><.*>*}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <,__.*>? <(Immediately|IMMEDIATELY|immediately)__.*> <,__.*>? <(If|IF|if)__.*> <(It|IT|it)__.*> <(So|SO|so)__.*> <(Chooses|CHOOSES|chooses)__.*> <,__.*>? (<(And|AND|and)__.*> <(In|IN|in)__.*> <(Its|ITS|its)__.*> <(Sole|SOLE|sole)__.*> <(And|AND|and)__.*> <(Absolute|ABSOLUTE|absolute)__.*> <(Discretion|DISCRETION|discretion)__.*>)? <,__.*>? <TERM_KW> <.*>*}
    {<MPARTY> <(Also|ALSO|also)__.*>? <(May|MAY|may|Can|CAN|can)__.*> <TERM_KW> <(The|THE|the)__.*> <(License|LICENSE|license)__.*><.*>*}
    {<MPARTY> <(Reserves?|RESERVES?|reserves?)__.*> <(The|THE|the)__.*> <(Right|RIGHT|right)__.*> (<,__.*> <.*>* <,__.*>)? <(To|TO|to)__.*> <.*>* <TERM_KW>}
    {<(This|THIS|this)__.*> <.*> <(Will|WILL|will)__.*>  <TERM_KW> <(If|IF|if)__.*> <MPARTY> <(Fails?|FAILS?|fails?)__.*> <.*>*}
    {<MPARTY> <,__.*> <.*>* <,__.*> <(Reserves|RESERVES|reserves)__.*> <(The|THE|the)__.*> <(Rights?|RIGHTS?|rights?)__.*> <(To|TO|to)__.*> <TERM_KW>}
    {<(This|THIS|this|The|THE|the)__.*> <.*> <(Is|IS|is)__.*> <(Effective|EFFECTIVE|effective)__.*> <(Until|UNTIL|until)__.*> (<(Suspended|SUSPENDED|suspended)__.*> <(Or|OR|or)__.*>)? <(Terminated|TERMINATED|terminated)__.*> <.*>*}
    {<MPARTY> <(Has|HAS|has|Have|HAVE|have)__.*> <(The|THE|the|A|a)__.*> <(Rights?|RIGHTS?|rights?)__.*><(To|TO|to)__.*> <TERM_KW>}
    {<MPARTY> <(License|LICENSE|license)__.*> <TERM_KW>}
    {<(At|AT|at)__.*> <MPARTY> <'s__.*> <(Option|OPTION|option)__.*> <,__,>? <(Shall|SHALL|shall)__.*> <TERM_KW>}
    {<(In|IN|in)__.*> <(Addition|ADDITION|addition)__.*> <(TO|To|to)__.*> <MPARTY> <'s__.*>? <(Other|OTHER|other)__.*> <(Rights|RIGHTS|rights)__.*> <,__,>? <(It|IT|it)__.*> <(May|MAY|may)__.*> <TERM_KW>}
    {<MPARTY> <(Agrees|AGREES|agrees)__.*> <(Not|NOT|not)__.*> <(To|TO|to)__.*> <TERM_KW> <.*>* <(Unless|UNLESS|unless)__.*>}
    {<MPARTY> <(Elects|ELECTS|elects)__.*> <(To|TO|to)__.*> <TERM_KW>}
    {<MPARTY> (<,__,> <.*>*)? <(Is|IS|is)__.*> <(Entitled|ENTITLED|entitled)__.*> (<,__,> <.*>*)? <(To|TO|to)__.*> <.*>* <TERM_KW>}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also)__.*>? <(Delete|DELETE|delete|Disable|DISABLE|disable)__.*> <.*>* <(Account|ACCOUNT|account)__.*>}
    {<MPARTY> <(May|MAY|may|Can|CAN|can)__.*> <(Also|ALSO|also)__.*>? <(Stop|STOP|stop)__.*>}
{% endif %}



PARTIAL_TERMINATION:
{% if both %}
    {<BOTH_PARTIES> <(May|may|MAY|Can|CAN|can)__.*> <TERM_KW> <(The|THE|the)__.*> <(Premium|PREMIUM|premium)__.*> <(Service|SERVICE|service)__.*>}
{% else %}
    {<MPARTY> <(May|may|MAY|Can|CAN|can)__.*> <TERM_KW> <(The|THE|the)__.*> <(Premium|PREMIUM|premium)__.*> <(Service|SERVICE|service)__.*>}
{% endif %}


"""
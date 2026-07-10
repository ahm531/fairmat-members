from nomad.config.models.plugins import ParserEntryPoint


class FAIRmatMembersParserEntryPoint(ParserEntryPoint):
    def load(self):
        from fairmat_members.parsers.parser import FAIRmatMembersParser

        # Do NOT pass model_dump() kwargs – MatchingParser only needs its own
        # constructor args and picks up entry-point metadata at the framework
        # level.  Passing the full pydantic dict would forward unrecognised
        # fields (id, entry_point_type, aliases, …) that have no meaning for
        # the parser class itself.
        return FAIRmatMembersParser()


parser_entry_point = FAIRmatMembersParserEntryPoint(
    name='FAIRmatMembersParser',
    description=(
        'Parses a FAIRmat member directory Excel or CSV file '
        'into individual Person entries.'
    ),
    # mainfile_name_re alone is sufficient to select the right files.
    # The MIME regex is omitted: NOMAD defaults mainfile_mime_re to '.*'
    # (match everything) in ParserEntryPoint, so CSV and Excel are both
    # accepted without an explicit MIME filter.
    mainfile_name_re=r'(?i).*mem.*\.(xlsx|xls|csv)$',
)

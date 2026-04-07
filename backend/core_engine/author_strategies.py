import re


def _split_affiliation_line(line: str) -> list:
    """Split long comma-separated affiliation into shorter chunks for IEEE blocks.

    This helps reduce block width so multi-author rows are less likely to wrap.
    """
    clean = line.strip()
    if not clean:
        return []

    if ',' not in clean:
        return [clean]

    parts = [p.strip() for p in clean.split(',') if p.strip()]
    if len(parts) <= 1:
        return [clean]

    chunks = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            chunks.append(f"{parts[i]}, {parts[i+1]}")
            i += 2
        else:
            chunks.append(parts[i])
            i += 1
    return chunks

class AuthorBlockStrategy:
    """Base strategy for generating author block in various LaTeX templates."""
    def generate(self, authors: list) -> str:
        raise NotImplementedError

class IEEEAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        """Generate author block in IEEEtran format."""
        symbol_only_re = re.compile(r'^[*†‡]+$')
        email_re = re.compile(r'[\w\.\-\+]+@[\w\.\-]+')

        block = "\\author{\n"
        parts = []
        for author in authors:
            name = author['name']
            has_corresponding_marker = False
            emails = []

            for aff in author.get('affiliations', []):
                clean = aff.strip()
                if not clean:
                    continue
                if symbol_only_re.match(clean):
                    has_corresponding_marker = True
                    continue
                for em in email_re.findall(clean):
                    if em not in emails:
                        emails.append(em)

            if has_corresponding_marker:
                name += "\\textsuperscript{*}"

            auth_str = f"\\IEEEauthorblockN{{{name}}}"
            if author.get('affiliations'):
                affil_lines = []
                for aff in author['affiliations']:
                    sub_lines = [s.strip() for s in aff.split('\n') if s.strip()]
                    for sl in sub_lines:
                        if symbol_only_re.match(sl):
                            continue
                        if '@' in sl:
                            for em in email_re.findall(sl):
                                if em not in emails:
                                    emails.append(em)
                            continue
                        compact = re.sub(r'\s{2,}', ' ', sl).strip()
                        if compact:
                            affil_lines.append(f"\\textit{{{compact}}}")
                for em in emails:
                    affil_lines.append(f"\\texttt{{{em}}}")
                affil_text = " \\\\ ".join(affil_lines)
                auth_str += f"\n\\IEEEauthorblockA{{{affil_text}}}"
            parts.append(auth_str)
        block += " \\and\n".join(parts)
        block += "\n}"
        return block

class SpringerAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        """Generate author block in Springer LNCS format (\\author + \\institute)."""
        email_re = re.compile(r'[\w\.\-\+]+@[\w\.\-]+')
        symbol_only_re = re.compile(r'^[*†‡]+$')

        # Collect unique non-email, non-marker affiliations across all authors
        affil_map = {}  # affiliation text -> institute number
        all_emails = []
        for author in authors:
            for aff in author.get('affiliations', []):
                clean = aff.strip()
                if not clean:
                    continue
                if symbol_only_re.match(clean):
                    continue
                if email_re.search(clean):
                    for em in email_re.findall(clean):
                        if em not in all_emails:
                            all_emails.append(em)
                    continue
                if clean not in affil_map:
                    affil_map[clean] = len(affil_map) + 1

        # Build \author{...} block
        author_parts = []
        for author in authors:
            name = author['name']
            insts = []
            corr_marker = ''
            for aff in author.get('affiliations', []):
                clean = aff.strip()
                if not clean:
                    continue
                if symbol_only_re.match(clean):
                    corr_marker = clean[0]
                    continue
                if email_re.search(clean):
                    continue
                if clean in affil_map:
                    insts.append(str(affil_map[clean]))
            if insts:
                name += f"\\inst{{{','.join(insts)}}}"
            if corr_marker:
                name += corr_marker
            author_parts.append(name)

        author_block = "\\author{" + " \\and ".join(author_parts) + "}"

        # Build \institute{...} block
        if affil_map:
            inst_parts = []
            for aff_text in affil_map:
                entry = ", ".join([s.strip() for s in aff_text.split('\n') if s.strip()])
                inst_parts.append(entry)
            institute_text = " \\and ".join(inst_parts)
            if all_emails:
                institute_text += f"\\\\\n\\email{{{', '.join(all_emails)}}}"
            author_block += "\n\\institute{" + institute_text + "}"
        else:
            fallback = "Institution not specified"
            if all_emails:
                fallback += f"\\\\\n\\email{{{', '.join(all_emails)}}}"
            author_block += "\n\\institute{" + fallback + "}"

        return author_block

class ElsevierAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        """Generate author block in Elsevier format (\\author + \\affiliation)."""
        parts = []
        for author in authors:
            parts.append(f"\\author{{{author['name']}}}")
            for aff in author.get('affiliations', []):
                aff_clean = aff.strip()
                lines = [s.strip() for s in aff_clean.split('\n') if s.strip()]
                email_line = None
                plain_lines = []
                for line in lines:
                    if '@' in line:
                        email_line = line
                    else:
                        plain_lines.append(line)
                org = plain_lines[0] if plain_lines else aff_clean
                city = plain_lines[1] if len(plain_lines) > 1 else ''
                country = plain_lines[2] if len(plain_lines) > 2 else ''
                kv_parts = [f"organization={{{org}}}"]
                if city:
                    kv_parts.append(f"city={{{city}}}")
                if country:
                    kv_parts.append(f"country={{{country}}}")
                parts.append("\\affiliation{" + ",\n            ".join(kv_parts) + "}")
                if email_line:
                    parts.append(f"\\ead{{{email_line}}}")
        return "\n".join(parts)

class ACMAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        """Generate author block in ACM format."""
        parts = []
        for author in authors:
            parts.append(f"\\author{{{author['name']}}}")
            affs = author.get('affiliations', [])
            if affs:
                for aff in affs:
                    aff_clean = aff.strip()
                    lines = [s.strip() for s in aff_clean.split('\n') if s.strip()]
                    email_line = None
                    plain_lines = []
                    for line in lines:
                        if '@' in line:
                            email_line = line
                        else:
                            plain_lines.append(line)

                    # Respect explicit ACM fields if they already exist in input.
                    institution_match = re.search(r'\\institution\{([^}]*)\}', aff_clean)
                    city_match = re.search(r'\\city\{([^}]*)\}', aff_clean)
                    country_match = re.search(r'\\country\{([^}]*)\}', aff_clean)

                    institution = (
                        institution_match.group(1).strip()
                        if institution_match and institution_match.group(1).strip()
                        else (plain_lines[0] if plain_lines else 'University')
                    )
                    city = (
                        city_match.group(1).strip()
                        if city_match and city_match.group(1).strip()
                        else (plain_lines[1] if len(plain_lines) > 1 else 'Your City')
                    )
                    country = (
                        country_match.group(1).strip()
                        if country_match and country_match.group(1).strip()
                        else 'Vietnam'
                    )

                    aff_block = (
                        "\\affiliation{%\n"
                        f"  \\institution{{{institution}}}\n"
                        f"  \\city{{{city}}}\n"
                        f"  \\country{{{country}}}\n"
                        "}"
                    )
                    parts.append(aff_block)
                    if email_line:
                        parts.append(f"\\email{{{email_line}}}")
            else:
                parts.append(
                    "\\affiliation{%\n"
                    "  \\institution{University}\n"
                    "  \\city{Your City}\n"
                    "  \\country{Vietnam}\n"
                    "}"
                )
        return "\n".join(parts)

class MDPIAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        r"""Generate author block in MDPI format (\Author + \address)."""
        affil_map = {}
        affil_emails = {}
        for author in authors:
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                email_parts = []
                inst_parts = []
                for line in lines:
                    if '@' in line:
                        email_parts.append(line)
                    else:
                        inst_parts.append(line)
                key = ', '.join(inst_parts) if inst_parts else aff.strip()
                if key and key not in affil_map:
                    affil_map[key] = len(affil_map) + 1
                    if email_parts:
                        affil_emails[key] = '; '.join(email_parts)

        author_parts = []
        for author in authors:
            name = author['name']
            insts = []
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                inst_parts = [l for l in lines if '@' not in l]
                key = ', '.join(inst_parts) if inst_parts else aff.strip()
                if key in affil_map:
                    insts.append(str(affil_map[key]))
            if insts:
                name += " $^{" + ",".join(insts) + "}$"
            author_parts.append(name)
        block = "\\Author{" + ", ".join(author_parts) + "}"

        plain_names = [a['name'] for a in authors]
        block += "\n\\AuthorNames{" + ", ".join(plain_names) + "}"

        if affil_map:
            addr_parts = []
            for aff_text, num in affil_map.items():
                entry = f"$^{{{num}}}$ \\quad {aff_text}"
                email = affil_emails.get(aff_text)
                if email:
                    entry += f"; {email}"
                addr_parts.append(entry)
            block += "\n\\address{" + " \\\\\n".join(addr_parts) + "}"
        else:
            block += "\n\\address{~}"

        return block

class OSCMAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        r"""Generate author block in OSCM Journal format.
        OSCM uses: \author[*]{Name}{Affiliation, Country}{email}
        where [*] marks the corresponding author (first author by default).
        """
        parts = []
        for i, author in enumerate(authors):
            name = author['name']
            # Extract affiliation and email from the author's affiliations
            affil_text = ''
            email_text = ''
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                for line in lines:
                    if '@' in line:
                        if email_text:
                            email_text += '; ' + line
                        else:
                            email_text = line
                    else:
                        if affil_text:
                            affil_text += '; ' + line
                        else:
                            affil_text = line

            if not affil_text:
                affil_text = 'Affiliation, Country'
            if not email_text:
                email_text = 'email@example.com'

            # First author is corresponding author [*]
            star = '[*]' if i == 0 else ''
            parts.append(f'\\author{star}{{{name}}}\n  {{{affil_text}}}\n  {{{email_text}}}')

        return '\n\n'.join(parts)

class JOVAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        r"""Generate author block for JOV Journal format.
        JOV uses: \author{Family name}{First name(s)}{Institution}{Address}{homepage}{email}
        """
        parts = []
        for author in authors:
            name_parts = author['name'].split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 1 else ''
            family_name = name_parts[1] if len(name_parts) > 1 else author['name']
            
            affil_text = 'Institution'
            address_text = 'Address'
            email_text = 'email@example.com'
            
            affil_lines = []
            for aff in author.get('affiliations', []):
                lines = [s.strip() for s in aff.strip().split('\n') if s.strip()]
                for line in lines:
                    if '@' in line:
                        email_text = line
                    else:
                        affil_lines.append(line)
            
            if affil_lines:
                affil_text = affil_lines[0]
                if len(affil_lines) > 1:
                    address_text = ', '.join(affil_lines[1:])
                else:
                    address_text = ''
                    
            parts.append(
                f"\\author{{{family_name}}}{{{first_name}}}"
                f"{{{affil_text}}}{{{address_text}}}{{}}{{{email_text}}}"
            )
            
        return "\n".join(parts)


class GenericAuthorStrategy(AuthorBlockStrategy):
    def generate(self, authors: list) -> str:
        """Generate a generic \\author{} block with standard LaTeX commands."""
        affils = []
        for a in authors:
            for aff in a.get('affiliations', []):
                if aff.strip() and aff.strip() not in affils:
                    affils.append(aff.strip())
        affil_note = ""
        if affils:
            affil_note = "\\thanks{" + "; ".join(affils) + "}"
        names = [a['name'] for a in authors]
        block = "\\author{" + ", ".join(names)
        if affil_note:
            block += " " + affil_note
        block += "}"
        return block

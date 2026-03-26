%% ====================================================================
%% oscmjournalv2.0.cls — Operations and Supply Chain Management Journal
%% ====================================================================
%% Version 2.01, 2026/01/26
%% License: All rights reserved by OSCM Journal Team (oscm.help@gmail.com).
%%
%% ====================================================================
%%  HOW TO USE THIS TEMPLATE
%% ====================================================================
%%
%%  1. DOCUMENT CLASS
%%     ---------------------------------------------------------------
%%     \documentclass[review]{oscmjournalv2.0}     % anonymous, single-column
%%     \documentclass[preprint]{oscmjournalv2.0}   % single-column draft
%%     \documentclass[final]{oscmjournalv2.0}      % two-column camera-ready
%%
%%  2. JOURNAL METADATA  (override in your .tex preamble)
%%     ---------------------------------------------------------------
%%     \renewcommand{\JournalVolume}{19}
%%     \renewcommand{\JournalNumber}{2}
%%     \renewcommand{\JournalYear}{2026}
%%     \renewcommand{\FirstPage}{322}
%%     \renewcommand{\RunningHeader}{Smith \emph{et al.}: Short Title}
%%
%%  3. TITLE
%%     ---------------------------------------------------------------
%%     \title{Your Paper Title Here}
%%
%%  4. AUTHORS — use \author for each author
%%     ---------------------------------------------------------------
%%     \author{First M. Last}
%%       {Department, University, City, Country}
%%       {email@example.com}           % add [*] for corresponding author
%%
%%     Example with corresponding author:
%%       \author[*]{Jane Doe}
%%         {Faculty of Engineering, MIT, USA}
%%         {jane@mit.edu}
%%
%%  5. KEYWORDS
%%     ---------------------------------------------------------------
%%     \keywords{keyword one, keyword two, keyword three}
%%
%%  6. DOCUMENT BODY
%%     ---------------------------------------------------------------
%%     \begin{document}
%%     \maketitle
%%     \begin{abstract} ... \end{abstract}
%%     \section{Introduction} ...
%%     \printbibliography[title={REFERENCES}]
%%
%%  7. BIOGRAPHIES (at end, before \end{document})
%%     ---------------------------------------------------------------
%%     \begin{strip}
%%     \biographies
%%     \begin{biography}{Author Name}
%%       Bio text here.
%%     \end{biography}
%%     \begin{biography}{Another Author}
%%       Bio text here.
%%     \end{biography}
%%     \end{strip}
%%
%%  8. TABLES — auto-styled; override per table with \tablestyle
%%     ---------------------------------------------------------------
%%     \begin{table}[htbp]
%%       \tablestyle[fontsize=8, linespacing=9, stretch=1.2, colsep=6pt]
%%       \caption{My Table}\label{tab:example}
%%       \begin{tabular}{lcc} ... \end{tabular}
%%     \end{table}
%%
%%     Use \thead{Header} for bold column headers.
%%     Use \WideTableDescWidth / \ColTableDescWidth for description columns.
%%
%%  9. BIBLIOGRAPHY — uses biblatex with APA style
%%     ---------------------------------------------------------------
%%     \addbibresource{mybibfile.bib}   % in preamble
%%     \printbibliography[title={REFERENCES}]  % at end
%%
%% 10. APPENDIX
%%     ---------------------------------------------------------------
%%     \onecolumn
%%     \appendix
%%     \section{APPENDIX}
%%
%% ====================================================================
%%  PACKAGES LOADED BY THIS CLASS (do NOT load again)
%% ====================================================================
%%  inputenc, times, graphicx, hyperref, xcolor, csquotes,
%%  amsmath, amssymb, multirow, booktabs, multicol, bm, array,
%%  diagbox, siunitx, ascmac, cuted, enumitem, etoolbox,
%%  pgfkeys, textcase, setspace, fancyhdr, lastpage, caption,
%%  biblatex (APA style), xpatch
%%
%% ====================================================================

\def\update{2026/01/26 v2.01}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{oscmjournalv2.0}[2026/01/26 OSCM Journal v2.0]

% ---- Layout options ------------------------------------------------
\newif\if@preprint
\@preprintfalse
\newif\if@review
\@reviewfalse

\DeclareOption{final}{\@preprintfalse\@reviewfalse}
\DeclareOption{preprint}{\@preprinttrue\@reviewfalse}
\DeclareOption{review}{\@preprinttrue\@reviewtrue}
\ExecuteOptions{final}
\ProcessOptions\relax


%% ============================================================
%% CONFIGURABLE PARAMETERS
%% Override any of these in your .tex file with \renewcommand
%% ============================================================

%% --- Journal identity ---
\newcommand{\JournalName}{Operations and Supply Chain Management}
\newcommand{\ISSN}{1979-3561}
\newcommand{\EISSN}{2759-9363}

%% --- Paper-specific (override in your .tex) ---
\newcommand{\JournalVolume}{00}
\newcommand{\JournalNumber}{0}
\newcommand{\JournalYear}{2023}
\newcommand{\RunningHeader}{OSCM, \emph{et al.}: OSCM \LaTeX~Template}
\newcommand{\FirstPage}{1}
\newcommand{\LastPage}{\pageref*{LastPage}}

%% --- Body text ---
\newcommand{\BodyFontSize}{10}          % pt
\newcommand{\BodyLineSpacing}{12}       % pt (baseline skip)
\newcommand{\BodyFontFamily}{ptm}       % Times Roman

%% --- Title ---
\newcommand{\TitleFontSize}{22}         % pt
\newcommand{\TitleFontFamily}{phv}      % Helvetica
\newcommand{\AuthorFontSize}{12}        % pt
\newcommand{\AuthorLineSpacing}{14}     % pt

%% --- Author separator ---
\newcommand{\authorsep}{\vspace{0.75em}}

%% --- Abstract ---
\newcommand{\AbstractHeadingSize}{14}   % pt
\newcommand{\AbstractFontSize}{9}       % pt
\newcommand{\AbstractLineSpacing}{9}    % pt
\newcommand{\AbstractSpaceAbove}{-7pt}  % space between heading and text

%% --- Section headings ---
\newcommand{\SectionFontSize}{14}       % pt
\newcommand{\SectionLineSpacing}{16}    % pt
\newcommand{\SectionSpaceBefore}{-0.75ex plus -0.5ex minus -.1ex}
\newcommand{\SectionSpaceAfter}{0.5ex plus .1ex}
\newcommand{\SubsectionFontSize}{12}    % pt
\newcommand{\SubsectionSpaceBefore}{-0.5ex plus -0.25ex minus -.1ex}
\newcommand{\SubsectionSpaceAfter}{0.25ex plus .1ex}
\newcommand{\SubsubsectionFontSize}{10} % pt
\newcommand{\SubsubsectionSpaceBefore}{-0.25ex plus -0.1ex minus -.05ex}
\newcommand{\SubsubsectionSpaceAfter}{0.1ex plus .05ex}

%% --- Tables ---
\newcommand{\TableFontSize}{7}          % pt
\newcommand{\TableLineSpacing}{7}       % pt
\newcommand{\TableArrayStretch}{1.0}    % row height multiplier
\newcommand{\TableFontFamily}{phv}      % Helvetica
\newcommand{\TableColSep}{5pt}          % column padding

%% --- Lists (itemize/enumerate) ---
\newcommand{\ListLeftMargin}{1.5em}     % indentation of bullet/number
\newcommand{\ListItemSep}{1pt}          % space between items

%% --- Biographies ---
\newlength{\BiographySepBefore}   \setlength{\BiographySepBefore}{1em}
\newlength{\BiographySepAfter}    \setlength{\BiographySepAfter}{2em}
\newlength{\BiographyItemSep}     \setlength{\BiographyItemSep}{5em}

%% ============================================================
%% END CONFIGURABLE PARAMETERS
%% ============================================================


%% Derived settings
\newcommand{\ShortHeader}{\RunningHeader \\ \JournalName~\JournalVolume(\JournalNumber), \FirstPage--\LastPage~\copyright~\JournalYear}


% ---- Load base class -----------------------------------------------
\if@preprint
    \LoadClass[a4paper,onecolumn,twoside]{article}
\else
    \LoadClass[a4paper,twocolumn,twoside]{article}
\fi


%% ============================================================
%% REQUIRED PACKAGES
%% ============================================================

\usepackage[utf8]{inputenc}
\usepackage{times}
\usepackage{cuted}
\usepackage{enumitem}
\usepackage{etoolbox}

%% In single-column (preprint) mode, the strip environment from cuted
%% does not work.  Redefine it as a no-op so content renders normally.
\if@preprint
    \renewenvironment{strip}{}{}
\fi

%% --- Math ---
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{bm}

%% --- Tables ---
\usepackage{multirow}
\usepackage{booktabs}
\usepackage{array}
\usepackage{diagbox}

%% --- Graphics & Color ---
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{multicol}

%% --- Text utilities ---
\usepackage{csquotes}
\usepackage{ascmac}

%% --- Units ---
\usepackage{siunitx}
\sisetup{
    group-separator={,},
    group-minimum-digits=4,
    round-mode=places,
    round-precision=2,
    detect-all
}

%% --- Hyperlinks (load near-last before biblatex) ---
\usepackage{hyperref}
\hypersetup{
    colorlinks=false,
    linkbordercolor={white},
    citebordercolor={white},
    urlbordercolor={white},
}


%% ============================================================
%% PAGE LAYOUT
%% ============================================================

\setlength{\headheight}{32pt}
\setlength{\topmargin}{-2cm}
\setlength{\textheight}{25.5cm}
\setlength{\textwidth}{17.6cm}
\setlength{\oddsidemargin}{-0.7cm}
\setlength{\evensidemargin}{-0.7cm}
\setlength{\columnsep}{2em}


%% ============================================================
%% AUTHOR SYSTEM
%% ============================================================
%% Usage:
%%   \author[*]{Name}{Affiliation}{email}   — corresponding author
%%   \author{Name}{Affiliation}{email}       — co-author
%%
%% Internally builds \@authorinfo for use by \maketitle.
%% Also supports legacy \authorinfo{...} for backward compatibility.
%% Legacy \author is kept as an alias.

\newcommand{\authorinfo}[1]{\def\@authorinfo{#1}}

% Internal storage: accumulate author blocks
\def\@authorinfo{}
\newcounter{oscm@authorcount}

% Redefine \author to accept the OSCM 4-arg form.
% In review mode, author info is replaced with "Anonymous".
\if@review
    \renewcommand{\author}[4][]{%
        \ifnum\value{oscm@authorcount}=0
            \def\@authorinfo{\textbf{Anonymous Author(s)}\\[0.5em]%
                \textit{(Author information withheld for double-blind review)}}%
        \fi
        \stepcounter{oscm@authorcount}%
    }
\else
    \renewcommand{\author}[4][]{%
        \stepcounter{oscm@authorcount}%
        \ifnum\value{oscm@authorcount}>1
            \g@addto@macro\@authorinfo{\authorsep}%
        \fi
        \begingroup
            \def\@tempcorr{#1}%
            \def\@tempstar{*}%
            \ifx\@tempcorr\@tempstar
                \g@addto@macro\@authorinfo{%
                    \textbf{#2}\\#3\\Email: #4~({\it Corresponding Author})\\%
                }%
            \else
                \g@addto@macro\@authorinfo{%
                    \textbf{#2}\\#3\\Email: #4\\%
                }%
            \fi
        \endgroup
    }
\fi

% Backward-compatible alias
\let\oscmauthor\author

\newcommand{\keywords}[1]{%
    \def\@keywords{\textit{#1}}
}


%% ============================================================
%% TITLE / MAKETITLE
%% ============================================================

\if@preprint
    \usepackage{lineno}
    \if@review
        % Review mode: double-spacing, line numbers, and doubled heading spacing
        \renewcommand{\normalsize}{\fontsize{\BodyFontSize}{24}\fontfamily{\BodyFontFamily}\selectfont}
        \AtBeginDocument{\linenumbers}
        \renewcommand{\SectionSpaceBefore}{-3.5ex plus -1ex minus -.2ex}
        \renewcommand{\SectionSpaceAfter}{0.75ex plus .1ex}
        \renewcommand{\SubsectionSpaceBefore}{-2.5ex plus -0.5ex minus -.2ex}
        \renewcommand{\SubsectionSpaceAfter}{0.5ex plus .1ex}
        \renewcommand{\SubsubsectionSpaceBefore}{-1.5ex plus -0.25ex minus -.1ex}
        \renewcommand{\SubsubsectionSpaceAfter}{0.25ex plus .05ex}
    \else
        \renewcommand{\normalsize}{\fontsize{\BodyFontSize}{\BodyLineSpacing}\fontfamily{\BodyFontFamily}\selectfont}
    \fi
    \renewcommand{\maketitle}{%
        \begin{center}
            \fontsize{\TitleFontSize}{\TitleFontSize}\fontfamily{\TitleFontFamily}\fontseries{b}\fontshape{n}\selectfont
            \@title
            \medskip \\
            \vspace{0.5em}
            \fontsize{\AuthorFontSize}{\AuthorLineSpacing}\fontfamily{\BodyFontFamily}\fontseries{n}\selectfont
            \@authorinfo
        \end{center}%
        \vspace{2em}
    }
\else
    \renewcommand{\normalsize}{\fontsize{\BodyFontSize}{\BodyLineSpacing}\fontfamily{\BodyFontFamily}\selectfont}
    \renewcommand{\maketitle}{%
        \twocolumn[%
            \begin{center}
                \fontsize{\TitleFontSize}{\TitleFontSize}\fontfamily{\TitleFontFamily}\fontseries{b}\fontshape{n}\selectfont
                \@title
                \medskip \\
                \vspace{0.5em}
                \fontsize{\AuthorFontSize}{\AuthorLineSpacing}\fontfamily{\BodyFontFamily}\fontseries{n}\selectfont
                \@authorinfo
            \end{center}%
            \vspace{2em}
        ]%
    }
\fi


%% ============================================================
%% LIST FORMATTING
%% ============================================================

\setlist{nosep, topsep=0pt, partopsep=0pt, parsep=0pt, itemsep=\ListItemSep, leftmargin=\ListLeftMargin}


%% ============================================================
%% TABLE DEFAULTS
%% ============================================================

\setlength{\tabcolsep}{\TableColSep}
\newcommand{\@applytablestyle}{%
    \renewcommand{\arraystretch}{\TableArrayStretch}%
    \fontsize{\TableFontSize}{\TableLineSpacing}\fontfamily{\TableFontFamily}\selectfont
}
\AtBeginEnvironment{table}{\@applytablestyle}
\AtBeginEnvironment{table*}{\@applytablestyle}

% Per-table style override: \tablestyle[fontsize=8,linespacing=9,stretch=1.2,colsep=4pt]
\usepackage{pgfkeys}
\pgfkeys{
    /tablestyle/.cd,
    fontsize/.store in=\ts@fontsize,
    linespacing/.store in=\ts@linespacing,
    stretch/.store in=\ts@stretch,
    colsep/.store in=\ts@colsep,
    fontsize/.default=\TableFontSize,
    linespacing/.default=\TableLineSpacing,
    stretch/.default=\TableArrayStretch,
    colsep/.default=\TableColSep,
}
\newcommand{\tablestyle}[1][]{%
    \pgfkeys{/tablestyle/.cd,
        fontsize=\TableFontSize,
        linespacing=\TableLineSpacing,
        stretch=\TableArrayStretch,
        colsep=\TableColSep,
        #1}%
    \fontsize{\ts@fontsize}{\ts@linespacing}\fontfamily{\TableFontFamily}\selectfont
    \renewcommand{\arraystretch}{\ts@stretch}%
    \setlength{\tabcolsep}{\ts@colsep}%
}

% Bold table header helper
\newcommand{\thead}[1]{\textbf{#1}}

% Default description column widths
\newcommand{\WideTableDescWidth}{14cm}
\newcommand{\ColTableDescWidth}{6cm}


%% ============================================================
%% SECTION FORMATTING
%% ============================================================

\setcounter{secnumdepth}{3}
\usepackage{textcase}

\renewcommand{\section}{%
    \@startsection{section}{1}{0pt}{\SectionSpaceBefore}%
    {\SectionSpaceAfter}{\fontsize{\SectionFontSize}{\SectionLineSpacing}\fontseries{b}\fontshape{n}\selectfont\centering\bfseries}%
}
\renewcommand{\@seccntformat}[1]{%
    \csname the#1\endcsname.
}
% Auto-uppercase section titles
\let\ori@section\section
\renewcommand{\section}{\@ifstar\@ssection\@nsection}
\newcommand{\@ssection}[1]{\ori@section*{\MakeTextUppercase{#1}}}
\newcommand{\@nsection}[1]{\ori@section{\MakeTextUppercase{#1}}}

\renewcommand{\subsection}{%
    \vspace{0.125em}
    \@startsection{subsection}{2}{0pt}{\SubsectionSpaceBefore}%
    {\SubsectionSpaceAfter}{\fontsize{\SubsectionFontSize}{0}\fontseries{b}\fontshape{it}\selectfont\itshape}%
}

\if@preprint
    \renewcommand{\subsubsection}{%
        \vspace{0.125em}
        \@startsection{subsubsection}{3}{0pt}{\SubsubsectionSpaceBefore}%
        {\SubsubsectionSpaceAfter}{\fontsize{\SubsubsectionFontSize}{0}\fontseries{m}\fontshape{it}\selectfont}%
    }
\else
    \renewcommand{\subsubsection}{%
        \vspace{0.125em}
        \@startsection{subsubsection}{3}{0pt}{\SubsubsectionSpaceBefore}%
        {\SubsubsectionSpaceAfter}{\fontsize{\SubsubsectionFontSize}{0}\fontseries{m}\fontshape{it}\selectfont}%
    }
\fi


%% ============================================================
%% ABSTRACT
%% ============================================================

\usepackage{setspace}
\renewenvironment{abstract}{%
    \noindent\begin{center}
        \fontsize{\AbstractHeadingSize}{0}\fontfamily{\BodyFontFamily}\fontseries{b}\selectfont{ABSTRACT}
    \end{center}
    \vspace{\AbstractSpaceAbove}
    \fontsize{\AbstractFontSize}{\AbstractLineSpacing}\fontfamily{\BodyFontFamily}\fontseries{b}\selectfont
}{%
    \vspace{5pt}
    \newline
    \fontsize{\AbstractFontSize}{\AbstractLineSpacing}\fontfamily{\BodyFontFamily}\selectfont
    \noindent \textbf{Keywords:} {\fontseries{m}\selectfont\@keywords}
}


%% ============================================================
%% HEADERS AND FOOTERS
%% ============================================================

\usepackage{fancyhdr}
\usepackage{lastpage}
\pagestyle{fancy}
\fancyhf{}

\if@review
    % Review mode: no journal header, no running author header, just page numbers
    \fancypagestyle{firstpage}{
        \fancyhf{}
        \fancyfoot[C]{\thepage}
        \renewcommand{\headrulewidth}{0pt}
    }
    \fancypagestyle{subseqpages}{
        \fancyhf{}
        \fancyfoot[C]{\thepage}
        \renewcommand{\headrulewidth}{0pt}
    }
\else
    \fancypagestyle{firstpage}{
        \fancyhead[L]{%
            \fontsize{9}{11}\selectfont
            \fontfamily{\BodyFontFamily}\selectfont
            \textbf{\MakeUppercase{\JournalName}}\\
            Vol. \JournalVolume, No. \JournalNumber, \JournalYear, pp. \FirstPage~--~\LastPage\\
            ISSN \ISSN $\mid$ EISSN \EISSN
        }
        \fancyhead[R]{%
            \includegraphics[height=0.8cm]{figs/oscm.png}
        }
        \renewcommand{\headrulewidth}{0pt}
    }
    \fancypagestyle{subseqpages}{
        \fancyhf{}
        \fancyhead[LE,RO]{\thepage}
        \fancyhead[LO,RE]{\ShortHeader}
    }
\fi

\AtBeginDocument{
    \setcounter{page}{\FirstPage}
    \thispagestyle{firstpage}
    \pagestyle{subseqpages}
}


%% ============================================================
%% FIGURE AND TABLE CAPTIONS
%% ============================================================

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{period}{\hspace*{1ex}}
\captionsetup[figure]{font=normal,labelfont={bf},labelsep=period,justification=centering,singlelinecheck=false}
\captionsetup[table]{position=top,labelsep=period,font=normal,labelfont={bf},justification=raggedright,skip=2pt,singlelinecheck=false}


%% ============================================================
%% BIOGRAPHIES
%% ============================================================

\if@review
    % In review mode, biographies are hidden entirely.
    \newcommand{\biographies}{}
    \newenvironment{biography}[1]{\setbox0\vbox\bgroup}{\egroup}
\else
    \newcommand{\biographies}{%
        \raggedbottom
        \vspace*{\BiographySepBefore}
        \hrule
        \vspace*{\BiographySepAfter}
    }
    \newenvironment{biography}[1]{%
        \par\vspace*{\BiographyItemSep}\noindent{\small\textbf{#1} }%
        \small\ignorespaces
    }{%
        \par
    }
\fi


%% ============================================================
%% BIBLIOGRAPHY (biblatex, APA style)
%% ============================================================

\usepackage[style=apa]{biblatex}
\DefineBibliographyStrings{english}{%
    andothers = {\em et\addabbrvspace al\adddot}
}

\renewcommand{\labelnamepunct}{\addspace}

\DeclareDelimFormat[bib]{finalnamedelim}{%
  \ifthenelse{\value{listcount}>\maxprtauth}
    {}
    {\ifthenelse{\value{liststop}>2}
       {\finalandcomma\addspace\bibstring{and}\space}
       {\addspace\bibstring{and}\space}}}

\DeclareDelimFormat[bib]{finalnamedelim:apa:family-given}{%
  \ifthenelse{\value{listcount}>\maxprtauth}
    {}
    {\ifthenelse{\ifcurrentname{groupauthor}\AND%
                 \value{liststop}=2}
     {\addspace\bibstring{and}\space}
     {\finalandcomma\addspace\bibstring{and}\space}}}

\usepackage{xpatch}
\xpatchbibdriver{article}
  {\usebibmacro{title}%
   \newunit}
  {\usebibmacro{title}%
   \printunit{\addcomma\space}}
  {}
  {}

\AtEveryBibitem{\clearfield{number}}

\DeclareFieldFormat[article]{volume}{\apanum{#1}}

\renewbibmacro*{journal+issuetitle}{%
  \usebibmacro{journal}%
  \setunit*{\space}%
  \iffieldundef{series}
    {}
    {\newunit
     \printfield{series}%
     \setunit{\addspace}}%
  \usebibmacro{volume+number+eid}%
  \setunit{\addspace}%
  \usebibmacro{issue}%
  \setunit{\addcolon\space}%
  \usebibmacro{issue}%
  \newunit}

%%%%%
%% nusaart.cls
%% LaTeX class file for NUSA: Linguistic studies of languages in and around 
%% Indonesia (online edition ISSN 2187-7297; printed edition ISSN 0126-2874)
%% http://www.aa.tufs.ac.jp/en/publications/nusa
%%
%% Created and maintained by Lian Tze LIM (liantze@gmail.com) and Hiroki Nomoto (nomoto@tufs.ac.jp)
%% v0.1 September 21 2014
%% v0.2 September 26 2014 (HN)
%% v0.3 October 5 2014 (HN): Positions of tables/figures and their captions forced by caption and floatrow.
%% v0.4 November 15 2014 (HN): Hyperref added for bookmarks and links.
%% v0.5 December 18 2014 (HN): Footnote number size reduced to \scriptsize.
%% v1.1 September XX 2018 (HN): Infobox items, volumes with no special topic and editor, doi

\ProvidesClass{nusaart}[2018/09/03 v1.1]
\LoadClass[12pt,twoside,a4paper,titlepage]{article}
\RequirePackage{etoolbox}
\RequirePackage{ragged2e}

\RequirePackage[T1]{fontenc}
\RequirePackage{mathptmx}
\RequirePackage{helvet}

% Top and bottom margins are 2.5cm, left and right margins are 3cm with no 
% gutter. Header is 1.25cm from edge, footer is 1.5. Paper size is A4 (it is 
% reduced to JISB5 for printing).
% header is 1.25cm from edge, so headsep = 2.5 - 1.25 - 14pt
% footer is only relevant for first page which depends on the height of
% author info -- see later.)
\RequirePackage{calc}
\RequirePackage[a4paper, hmargin=3cm, vmargin=2.5cm,
	headheight=12pt, headsep=1.25cm-\headheight]{geometry}

\def\@pURL{!INSERT PERMANENTURL!}
\def\@doi{!INSERT DOI!}
\def\@jourvolume{!INSERT VOLUME NUMBER!}
\def\@jourvolumetitle{!INSERT VOLUME TITLE!}
\def\@startpage{!INSERT START PAGE NUMBER!}
\def\@endpage{!INSERT END PAGE NUMBER!}
\def\@runningtitle{!INSERT RUNNING TITLE!}
\def\@headerauthor{!INSERT HEADER AUTHOR!}
\def\@footerauthor{!INSERT FOOTER AUTHOR!}
\def\@editor{!INSERT EDITOR!}
\def\@affil{!INSERT AFFILIATION!}

\def\title#1{\gdef\@title{#1}}
\def\date#1{\gdef\@date{#1}}
\def\pURL#1{\gdef\@pURL{#1}}
\def\doi#1{\gdef\@doi{#1}}
\def\jourvolume#1{\gdef\@jourvolume{#1}}
\def\jourvolumetitle#1{\gdef\@jourvolumetitle{#1}}
\def\affil#1{\gdef\@affil{#1}}
%\def\editor#1{\gdef\@editor{#1}} %v0.1
\newcommand{\editor}[2][ed.]{\gdef\@editor{#2, #1}}
\def\startpage#1{\gdef\@startpage{#1}\setcounter{page}{#1}}
\def\endpage#1{\gdef\@endpage{#1}}

%% Shortened title, if available
\def\runningtitle#1{\gdef\@runningtitle{#1}}

%% Authors for the header and footer
\def\headerauthor#1{\gdef\@headerauthor{#1}}
\def\footerauthor#1{\gdef\@footerauthor{#1}}

\newbox{\infobox}
\newlength{\infoboxheight}
\AtEndPreamble{
%	\gdef\@footertext{\@footerauthor, \@date. `\@title'. In \@editor, ed. \emph{\@jourvolumetitle}. NUSA \@jourvolume: \@startpage--\@endpage. [Permanent URL: \@pURL]} %v0.1
%\gdef\@footertext{\@footerauthor, \@date. `\@title'. In \@editor{} \emph{\@jourvolumetitle}. NUSA \@jourvolume: \@startpage--\@endpage. [Permanent URL: \@pURL]} %v0.5
\gdef\@footertext{%
	\ifdefempty{\@jourvolumetitle}{\@footerauthor, \@date. `\@title'. NUSA \@jourvolume: \@startpage--\@endpage. [Permanent URL: \@pURL] [doi: \@doi]}{\@footerauthor, \@date. `\@title'. In \@editor{} \emph{\@jourvolumetitle}. NUSA \@jourvolume: \@startpage--\@endpage. [Permanent URL: \@pURL] [doi: \@doi]}}
	\savebox{\infobox}{\parbox[t]{\textwidth}{\@footertext}%
	}
	\settototalheight{\infoboxheight}{\usebox{\infobox}}

	%% first page only -- note the bottom margin
	\geometry{
		bottom=1.5cm+\infoboxheight+2.5ex,
		footskip=1.25ex+\baselineskip
	}
}

%% The title, the authors, the affiliations
\renewcommand{\maketitle}{%
	\begin{center}
	%% Title is sans serif 12pt, no bold
	\textsf{\@title}\par
	%% Author names are serif 12pt, no bold
	\@author\par
	%% Affiliations are serif 10pt, no bold
	{\footnotesize\@affil\par}
	\end{center}
	\thispagestyle{plain}
	% after the first page, add back to text height so that 
	% bottom margin is 2.5cm
	\global\advance\textheight by \infoboxheight
	\global\advance\textheight by 1.5ex
	\global\advance\textheight by -1cm
}

%% Abstract is 10pt serif, 1cm indent from both sides
\renewenvironment{abstract}
{\footnotesize\list{}{
	\setlength{\leftmargin}{1cm}%
	\setlength{\rightmargin}{\leftmargin}%
	}%
	\item\relax}
{\endlist}

%% Might as well redefine the quote environments too!
\renewenvironment{quote}
{\list{}{
	\setlength{\leftmargin}{1cm}%
	\setlength{\rightmargin}{\leftmargin}%
	}%
	\item\relax}
{\endlist}

\renewenvironment{quotation}
{\list{}{
	\setlength{\leftmargin}{1cm}%
	\setlength{\rightmargin}{\leftmargin}%
	}%
	\item\relax}
{\endlist}

\RequirePackage{enumitem}
\setlist[itemize]{nosep}
\setlist[enumerate]{nosep}

%% sectional titles
\RequirePackage{titlesec}
\titleformat{\section}{\sffamily\bfseries}{\thesection.}{.5em}{}
\titlespacing*{\section}{0pt}{*1.5}{0pt}
%\titleformat{\subsection}{\sffamily\bfseries}{\thesubsection}{.5em}{} %v0.1
\titleformat{\subsection}{\sffamily\bfseries\small}{\thesubsection}{.5em}{}
\titlespacing*{\subsection}{0pt}{*1.5}{0pt}
%\titleformat{\subsubsection}{\sffamily\footnotesize}{}{0pt}{} %v0.1
\titleformat{\subsubsection}{\sffamily\bfseries\footnotesize}{\thesubsubsection}{.5em}{}
\titlespacing*{\subsubsection}{0pt}{*1.5}{0pt}


%% no paragraph indent, 6pt before and after paragraphs
\RequirePackage[parfill]{parskip}


%% Running headers and footers
\RequirePackage{fancyhdr}
\fancyhf{}
\fancyhead[RO,LE]{\footnotesize\sffamily\thepage}
\fancyhead[CO]{\footnotesize\sffamily{\scshape\@headerauthor}: \ifdefempty{\@runningtitle}{\@title}{\@runningtitle}}
\fancyhead[CE]{\footnotesize\sffamily NUSA \@jourvolume, \@date}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\fancypagestyle{plain}{
	\fancyhf{}
	\renewcommand{\footrulewidth}{0.4pt}
	\cfoot{\noindent\justifying\@footertext}
} 
\pagestyle{fancy}

%% Footnotes
% From E-Ching Ng's ``A LaTeX setup''
\addtolength{\skip\footins}{12pt} % More space between body text and footnote rule
\addtolength{\footnotesep}{6pt}   % More space between footnote itmes
% Modified version of epltxfn.sty to get the footnote number in superscript (cf. section 6.8, ExPex documentation)
\RequirePackage{expex}
\def\everyfootnote{%
   \keepexcntlocal
   \excnt=1
   \lingset{exskip=1ex,interpartskip=0pt,exnotype=roman,sampleexno=,
      labeltype=alpha,labelanchor=numright,labeloffset=.6em,
      aboveglftskip=0pt,
      textoffset=.6em}
}
\renewcommand{\@makefntext}[1]{%
   \everyfootnote
   \parindent=1em
   \noindent
   \@textsuperscript{\scriptsize\@thefnmark}\enspace #1%
   
}


%% Float captions
%\RequirePackage[justification=raggedright,singlelinecheck=false]{caption} % v0.1
%\RequirePackage[justification=raggedright,singlelinecheck=false,skip=6pt]{caption} %v0.2
\RequirePackage[singlelinecheck=false,skip=6pt]{caption}
\captionsetup[table]{justification=raggedright,labelsep=period,font={bf}}
\captionsetup[figure]{justification=centering,labelsep=period,font={bf}}
\RequirePackage{floatrow}
\floatsetup[table]{style=plaintop,justification=raggedright}

%% Abbreviations list
\RequirePackage{multicol}
\RequirePackage{environ}
%% code modified from http://tex.stackexchange.com/questions/130097/automatically-set-description-list-labelwidth-based-on-widest-label
%% However, \global\setlength won't work if calc has been loaded (it has!)
%% so using \global\widest=@tempdima instead. See Heiko's comment in
%% https://groups.google.com/forum/#!topic/comp.text.tex/rrhG7EBsdyk
\newlength\widest
%\newcommand{\abbrev}[2]{\item[#1] #2} % v0.1
\newcommand{\abbrev}[3][\textsc]{\item[#1{#2}] #3}
\NewEnviron{abbreviations}{%
  \vbox{%
    \global\setlength\widest{0pt}%
    \def\item[##1]{%
      \settowidth\@tempdima{\textsc{##1}}%
      \ifdim\@tempdima>\widest\global\widest=\@tempdima\fi%
    }%
    \setbox0=\hbox{\BODY}%
  }
  \vspace*{-\baselineskip}
  \begin{multicols}{2}
  \begin{description}[
%  	nosep,font=\scshape\mdseries, % v0.1
  	nosep,font=\footnotesize\mdseries,
    leftmargin=\dimexpr\widest+0.5em\relax,
    labelindent=0pt,
    labelwidth=\widest]
  \BODY
  \end{description}
  \end{multicols}%
  \vspace*{-\baselineskip}
}

%% natbib commands with unified bibliography style from http://celxj.org/
\RequirePackage{natbib}[2007/10/30]
\bibliographystyle{unified}
%% Citation style is (author date:page) e.g. (Sneddon 2006:70)
\setcitestyle{authoryear,round,citesep={;},aysep={},yysep={,},notesep={:}}

%%Bookmarks and links
\RequirePackage[pdfusetitle]{hyperref}
\hypersetup{
     bookmarksnumbered=true,
     colorlinks=true,
     linkcolor=black,
     citecolor=blue,
     filecolor=black,
     urlcolor=black
}


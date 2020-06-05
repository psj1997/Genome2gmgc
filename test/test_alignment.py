import pytest
from gmgc_finder.alignment import identity_coverage


KNOWN_RESULTS=[
    {
    'query_nt': "ATGATGATGATGTGA"
  , 'query_aa': "MMMM"
  , 'target_nt': "ATGATGATGATGTGA"
  , 'target_aa': "MMMM"
  , 'result': "EXACT"
    },
    {
        'query_nt': "ATGCATACTTATCACACCTACCATACCTAC"
        , 'query_aa': "MHTYHTYHTY"
        , 'target_nt': "ATGCACACTTACCATACGTATCATACATAC"
        , 'target_aa': "MHTYHTYHTY"
        , 'result': "SIMILAR"
    },
    {
        'query_nt': "ATGCATACTTATCACACCTACCATACCTAC"
        , 'query_aa': "MHTYHTYHTY"
        , 'target_nt': "ATGCACTACCCCCATTATCACACGTAT"
        , 'target_aa': "MHYPHYHTY"
        , 'result': "MATCH"
    },
    {
        'query_nt': "ATGCATACTTATCACACCTACCATACCTAC"
        , 'query_aa': "MHTYHTYHTY"
        , 'target_nt': "ATGGAACCTGAGCCAGAACCC"
        , 'target_aa': "MEPEPEP"
        , 'result': "NO MATCH"
    },
    {
        # This is GMGC10.280_550_801.Y2705
        'target_nt': '''
ATGTCAGTTAATAAAGAATCGAAAAACGGGGTGGGCAGCGCCACTGTTGAAAAAACGCTGCCAAAGGGTG
GGGTATATGCCTCCCTGTTTGAAAAAATTAATTTAGCGCCGGTAGCTGAACTCGGTGATGTAAACGGGTT
TGATGATAATACCGTGATGGCCGAAACCTCTGCGGATGCGCGCGTCACTGCCGCAGTAAAAGTATTTATG
CAGTGTCTGCAAAATTCCGGGCAGAGGGTAGAGAAGCTGGATAAAACCATCCTCGACCACCATATTGCGG
AGCTGGATTTTCAGATTGGCCGTCAGCTTGATGAGGTCATGCATCATGACGCTTTTCAGCGCACGGAGAG
CATCTGGCGGGGCCTGAAATCGCTGGTGGATAAAACCGACTTTCGCCAGAACGTCAAGCTGGAACTGCTC
GACTTATCCAAAGAGGAGCTGCGCCAGGACTTCGAGGACTCCCCGGAAATCATCCAGAGCGGGCTGTACA
AGCAGACCTATATCGCGGAATACGACACCCCCGGCGGAGAACCCATAGCCGCCGTCATCTCCGCTTGGGA
GTTCGATGCCTCCGCGCAGGATGTGGCGCTGATGCGTAACATCTCGAAGGTCGCCGCTGCCGCCCACATG
CCGTTTATTGGCTCCGCAGGGCCGACATTCTTCTTAAAAGAGAATATGGAGCAGGTGGCAGCCATCAAGG
ATATCGGTAACTACTTCGACCGCGCGGAGTACATCAAATGGAAATCCTTCCGCGAAACCGATGACTCTCG
CTACCTCGGTCTGGTGATGCCGCGCGTGCTGGGACGTCTGCCGTACGGCCCGGATACCGTTCCGGTGCGC
AGCTTCAACTACGTTGAGCAGGTCAAAGGCCCGGATCACGACAAATACCTGTGGACCAACGCCTCGTTCG
CGTTCGCCGCCAATATGGTGAAAAGCTTCATCAATAACGGCTGGTGCGTGCAGATCCGTGGCCCACAGGC
TGGCGGTGCCGTGCAGGACCTGCCTATCCATCTGTACGATCTCGGCACCGGTAACCAGGTGAAGATCCCC
TCTGAGGTGATGATCCCGGAAACCCGCGAGTTTGAGTTCGCCAATCTTGGTTTCATCCCGCTCTCCTACT
ACAAGAACCGCGACTACGCCTGCTTCTTCTCGGCGAACTCCACCCAAAAACCGGCGCTGTATGACACGGC
AGATGCCACGGCCAACAGCCGCATCAATGCCCGCCTGCCATACATCTTCCTGCTGTCGCGTATTGCGCAC
TACCTCAAGCTTATCCAGCGGGAAAACATCGGAACCACTAAGGATCGCCGCCTGCTTGAGCTGGAGCTCA
ACACCTGGGTACGCGGTCTGGTCACCGAGATGACCGACCCGGGCGATGCCCTACAGGCCTCGCATCCGCT
GCGCGATGCAAAAGTGGTGGTGGAAGATATCGAGGACAATCCGGGTTTCTTCCGCGTGAAGCTCTACGCG
GTTCCGCATTTCCAGGTGGAAGGCATGGACGTCAATCTGTCGCTGGTCTCTCAGATGCCGAAGGCGAAAG
CGTAA'''.replace('\n', ''),
        'target_aa': '''
MSVNKESKNGVGSATVEKTLPKGGVYASLFEKINLAPVAELGDVNGFDDNTVMAETSADARVTAAVKVFM
QCLQNSGQRVEKLDKTILDHHIAELDFQIGRQLDEVMHHDAFQRTESIWRGLKSLVDKTDFRQNVKLELL
DLSKEELRQDFEDSPEIIQSGLYKQTYIAEYDTPGGEPIAAVISAWEFDASAQDVALMRNISKVAAAAHM
PFIGSAGPTFFLKENMEQVAAIKDIGNYFDRAEYIKWKSFRETDDSRYLGLVMPRVLGRLPYGPDTVPVR
SFNYVEQVKGPDHDKYLWTNASFAFAANMVKSFINNGWCVQIRGPQAGGAVQDLPIHLYDLGTGNQVKIP
SEVMIPETREFEFANLGFIPLSYYKNRDYACFFSANSTQKPALYDTADATANSRINARLPYIFLLSRIAH
YLKLIQRENIGTTKDRRLLELELNTWVRGLVTEMTDPGDALQASHPLRDAKVVVEDIEDNPGFFRVKLYA
VPHFQVEGMDVNLSLVSQMPKAKA'''.replace('\n', ''),

        'query_nt': '''
AAATACCTGTGGACCAACGCCTCGTTCGCCTTCGCCGCCAACATGGTAAAAAGCTTTATCAACAACGGCT
GGTGCGTGCAGATCCGTGGCCCGCAGGCTGGCGGTGCCGTGCAGGACCTGCCCATCCATCTGTATGACCT
CGGCACCGGCAACCAGGTAAAGATCCCCTCTGAGGTGATGATCCCGGAAACCCGCGAGTTTGAGTTTGCC
AACCTCGGTTTCATCCCGCTCTCCTACTACAAGAACCGCGACTACGCCTGCTTCTTCTCGGCAAACTCCA
CCCAAAAACCGGCGCTGTATGACACGGCGGATGCCACGGCCAACAGCCGCATCAATGCCCGCCTGCCGTA
CATCTTCCTGCTGTCGCGTATTGCGCACTACCTCAAGCTTATCCAGCGCGAAAATATCGGCACCACCAAG
GATCGCCGCCTGCTTGAGCTGGAGCTCAACACCTGGGTACGCGGTCTGGTGACCGAAATGACCGATCCGG
GGGATGCGCTGCAGGCCTCGCATCCGCTGCGCGATGCGAAAGTGGTGGTGGAAGATATCGAGGACAACCC
CGGTTTCTTCCGCGTGAAGCTCTACGCGGTGCCGCATTTCCAGGTGGAAGGCATGGACGTCAGTCTGTCG
CTG
'''.replace('\n', ''),
        'query_aa' : '''
KYLWTNASFAFAANMVKSFINNGWCVQIRGPQAGGAVQDLPIHLYDLGTGNQVKIPSEVM
IPETREFEFANLGFIPLSYYKNRDYACFFSANSTQKPALYDTADATANSRINARLPYIFL
LSRIAHYLKLIQRENIGTTKDRRLLELELNTWVRGLVTEMTDPGDALQASHPLRDAKVVV
EDIEDNPGFFRVKLYAVPHFQVEGMDVSLSL
'''.replace('\n', ''),
        'result' : 'SIMILAR', # it just misses being a MATCH
    },
]


@pytest.mark.parametrize("t", KNOWN_RESULTS)
def test_alignment(t):
        assert identity_coverage(t['query_nt'],t['query_aa'],t['target_nt'],t['target_aa']) == t['result']




import argparse
import sys
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import os
import requests
import pandas as pd
import json
from safeout import safeout
from tqdm import tqdm
import gzip
import bz2
import subprocess
from os import path
import tempfile
from pkg_resources import resource_string
import datetime
import time
import yaml
from .alignment import identity_coverage
from .gmgc_finder_version import __version__


def parse_args(args):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='GMGC-Finder')
    parser.add_argument('-i', '--input',required=False,help = 'Path to the input genome FASTA file.',dest='genome_fasta',
                        default = None)
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Output directory (will be created if non-existent)',
                        dest='output',
                        default = None)
    parser.add_argument('--nt_genes',
                        required=False,
                        help='Path to the input DNA gene file (FASTA format)',
                        dest='nt_input',
                        default=None)
    parser.add_argument('--aa_genes',
                        required=False,
                        help='Path to the input amino acid gene file (FASTA format)',
                        dest='aa_input',
                        default=None)
    return parser.parse_args()

def gene_prediction(fasta_input,output):

    print('Start gene prediction...')


    if os.path.splitext(fasta_input)[1] == '.bz2':
        output_file = bz2.BZ2File(fasta_input)
        open(output + '/input.fasta', "wb+").write(output_file.read())
        output_file.close()
        fasta_input = output + '/input.fasta'


    subprocess.check_call(
            ['prodigal',
                '-i', fasta_input,
                '-o', path.join(output, 'gene.coords.gbk'),
                '-a', path.join(output, 'prodigal_out.faa'),
                '-d', path.join(output, 'prodigal_out.fna')])

            # For short inputs, prodigal will output the warning
            #
            # ```Warning:  ideally Prodigal should be given at least 100000 bases for training.
            # You may get better results with the -p meta option.```
            #
            # Arguably, we could check this, but we default to the non `-p meta` call

    print('\nGene prediction done.\n')

def split_file(gene_path,output_dir,is_dna,max_size = 50):
    def split(handle):
        split_fasta = []
        records = list(SeqIO.parse(handle, "fasta"))
        index = 0
        if len(records) >= max_size:
            num_seq = 0
            for seq_record in records:
                rec1 = SeqRecord(Seq(str(seq_record.seq)), id=seq_record.id, description='')
                split_fasta.append(rec1)
                num_seq += 1
                if num_seq == max_size:
                    num_seq = 0
                    index += 1
                    if is_dna is True:
                        SeqIO.write(split_fasta, output_dir + '/split_{}.fna'.format(index), 'fasta')
                    else:
                        SeqIO.write(split_fasta, output_dir + '/split_{}.faa'.format(index), 'fasta')
                    split_fasta = []
            if split_fasta != []:
                index += 1
                if is_dna is True:
                    SeqIO.write(split_fasta, output_dir + '/split_{}.fna'.format(index), 'fasta')
                else:
                    SeqIO.write(split_fasta, output_dir + '/split_{}.faa'.format(index), 'fasta')
        else:
            index += 1
            for seq_record in records:
                rec1 = SeqRecord(Seq(str(seq_record.seq)), id=seq_record.id, description='')
                split_fasta.append(rec1)
            if is_dna is True:
                SeqIO.write(split_fasta, output_dir + '/split_{}.fna'.format(index), 'fasta')
            else:
                SeqIO.write(split_fasta, output_dir + '/split_{}.faa'.format(index), 'fasta')
        return index

    if not os.path.exists(gene_path):
        raise Exception("Not exist the file!")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.path.splitext(gene_path)[1] == '.gz':
        with gzip.open(gene_path, "rt") as handle:
            index = split(handle)
            return index

    if os.path.splitext(gene_path)[1] == '.bz2':
        with bz2.open(gene_path, "rt") as handle:
            index = split(handle)
            return index

    index = split(gene_path)
    return index




def query_gmgc(fasta_file,max_try = 10):
    if not os.path.exists(fasta_file):
        raise Exception("Missing file '{}'".format(fasta_file))

    if len(list(SeqIO.parse(fasta_file, "fasta"))) == 0:
        raise Exception("Input FASTA file '{}' file is empty!".format(fasta_file))

    for try_index in range(max_try):
        try:
            parameter = {'mode': 'besthit', 'return_seqs': True}
            fasta = {'fasta': open('{}'.format(fasta_file), 'rb')}
            besthit = requests.post('http://gmgc.embl.de/api/v1.0/query/sequence', data = parameter, files = fasta)
        except Exception:
            print('GMGC-Finder query failed {} times!'.format(try_index+1))
            time.sleep(60)
        else:
            return besthit
    return None


def realignment(dna_path,aa_path,besthit):
    def alignment(record_dna,record_aa,hit_index,dna = False):
            hit_result = []
            if dna == True:
                query_dna = str(record_dna.seq)
            else:
                query_dna = ''
            query_aa = str(record_aa.seq)
            query_name = hit_index['query_name']
            if hit_index['hits'] != []:
                hit_gene_id = hit_index['hits'][0]['gene_id']
                target_dna = hit_index['hits'][0]['dna_sequence']
                target_aa =  hit_index['hits'][0]['protein_sequence']
                if target_aa and target_dna is not None:
                    realign_result = identity_coverage(query_dna,query_aa,target_dna,target_aa)
                    hit_result.extend([query_name,hit_gene_id,realign_result,target_dna,target_aa])
                else:
                    hit_result.extend([query_name, None, 'NO HIT', None, None])
            return hit_result

    results = []
    if dna_path is not None:
        for record_dna, record_aa, hit_index in zip(SeqIO.parse(dna_path,'fasta'),
                                                    SeqIO.parse(aa_path,'fasta'),
                                                    besthit):
            hit_result = alignment(record_dna,record_aa,hit_index,dna = True)
            results.append(hit_result)
    else:
        for  record_aa, hit_index in zip(SeqIO.parse(aa_path,'fasta'),
                                                    besthit):
            hit_result = alignment('',record_aa,hit_index,dna=False)
            results.append(hit_result)
    return results

def gene_num(gene):
    """
    return the number of sequence in a file(fasta, .gz , .bz2)
    """
    if os.path.splitext(gene)[1] == '.gz':
        with gzip.open(gene, "rt") as handle:
            return len(list(SeqIO.parse(handle, "fasta")))

    if os.path.splitext(gene)[1] == '.bz2':
        with bz2.open(gene, "rt") as handle:
            return len(list(SeqIO.parse(handle, "fasta")))

    return len(list(SeqIO.parse(gene, "fasta")))


def query_genome_bin(hit_table):
    hit_gene_id = hit_table['gene_id'].tolist()
    genome_bin_dict = {}
    for gene_id in hit_gene_id:
        genome_bin = requests.get('http://gmgc.embl.de/api/v1.0/unigene/{}/genome_bins'.format(gene_id))
        genome_bin = json.loads(bytes.decode(genome_bin.content))['genome_bins']
        for bin in genome_bin:
            if bin not in genome_bin_dict:
                genome_bin_dict[bin] = 1
            else:
                genome_bin_dict[bin] += 1
    genome_bin = pd.DataFrame.from_dict(genome_bin_dict,orient='index',columns=['times_gene_hit'])
    genome_bin = genome_bin.reset_index().rename(columns={'index':'genome_bin'})
    return genome_bin

def sha256sum(filname):
    import hashlib
    with open(filname, "rb") as f:
        sha256obj = hashlib.sha256()
        sha256obj.update(f.read())
        hash_value = sha256obj.hexdigest()
        return hash_value

def input_metadata(fpath):
    return {
            'input-path': fpath,
            'full_path': os.path.abspath(fpath),
            'mtime': str(time.ctime(os.path.getmtime(fpath))),
            'file-size': os.path.getsize(fpath),
            'sha256': sha256sum(fpath)
            }


def convert_command(command):
    command_line = 'gmgc-finder '
    for parameter in command:
        if command[parameter] is not None:
            command_line = command_line + '-'+ parameter + ' '
            command_line = command_line + command[parameter] + ' '
    return command_line

def main(args=None):

    start = datetime.datetime.now()

    if args is None:
        args = sys.argv
    args = parse_args(args)

    command_args = vars(args)
    command_line = convert_command(command_args)
    out = args.output
    if not os.path.exists(out):
        os.makedirs(out)

    with tempfile.TemporaryDirectory() as tmpdirname:
        if args.genome_fasta is not None:
            gene_prediction(args.genome_fasta,out)

            split_file(out + '/prodigal_out.faa',
                                   output_dir=tmpdirname + '/split_file',is_dna=False)
            num_split = split_file(out + '/prodigal_out.fna',
                                   output_dir=tmpdirname + '/split_file',is_dna=True)
        else:
            if args.aa_input is None:
                raise Exception("Need to input protein gene file or a genome file!")

            else:
                if args.nt_input is not None:
                    assert gene_num(args.nt_input) == gene_num(args.aa_input), "Input dna and protein gene file must have the same sequence number."
                    split_file(args.aa_input,
                                           output_dir=tmpdirname + '/split_file',is_dna=False)
                    num_split = split_file(args.nt_input,
                                           output_dir=tmpdirname + '/split_file',is_dna=True)

                else:
                    num_split = split_file(args.aa_input,
                                           output_dir=tmpdirname + '/split_file',is_dna=False)
        hit_table = []
        print('Starting GMGC queries (total: {} batches to process)'.format(num_split))
        for index in tqdm(range(num_split)):
            besthit = query_gmgc(tmpdirname+'/split_file/split_{}.faa'.format(index+1))
            if besthit is not None:
                besthit = json.loads(bytes.decode(besthit.content))['results']
                if args.nt_input is not None:
                    hit_table_index = realignment(tmpdirname+'/split_file/split_{}.fna'.format(index+1),
                                                  tmpdirname+'/split_file/split_{}.faa'.format(index+1),besthit)
                else:
                    hit_table_index = realignment(None,tmpdirname+'/split_file/split_{}.faa'.format(index+1),besthit)
                hit_table.extend(hit_table_index)
        hit_table = pd.DataFrame(hit_table)
        hit_table.columns = ['query_name','gene_id','align_category','gene_dna','gene_protein']
        num_gene = hit_table.shape[0]


        summary = []
        summary.append('*'*30+'GMGC-Finder results summary table'+'*'*30)
        summary.append('- Processed {} genes'.format(num_gene))
        match_result = hit_table['align_category'].value_counts().to_dict()
        if 'EXACT' in match_result:
            summary.append(' -{0} ({1:.1%}) were found in the GMGC at above 95% nucleotide identity with at least 95% coverage'
                    .format(match_result['EXACT'], match_result['EXACT']/num_gene))
        else:
            summary.append(' -No genes were found in the GMGC at above 95% nucleotide identity with at least 95% coverage')

        if 'SIMILAR' in match_result:
            summary.append(' -{0} ({1:.1%}) were found in the GMGC at above 80% nucleotide identity with at least 80% coverage'
                    .format(match_result['SIMILAR'], match_result['SIMILAR']/num_gene))
        else:
            summary.append(' -No genes were found in the GMGC at above 80% nucleotide identity with at least 80% coverage')

        if 'MATCH' in match_result:
            summary.append(' -{0} ({1:.1%}) were found in the GMGC at above 50% nucleotide identity with at least 50% coverage'
                    .format(match_result['MATCH'], match_result['MATCH']/num_gene))
        else:
            summary.append(' -No genes were found in the GMGC at above 50% nucleotide identity with at least 50% coverage')

        no_match = match_result.get('NO MATCH', 0.0) + match_result.get('NO HIT', 0.0)
        if no_match:
            summary.append(' -{0} ({1:.1%}) had no match in the GMGC'
                        .format(no_match, no_match/num_gene))

        genome_bin = query_genome_bin(hit_table)
        summary.append('\n\n'+'*' * 30 + 'GMGC-Finder results genome_bin table' + '*' * 30+'\n\n')
        summary.append(' '*36+ 'genome bin'+' '*6+'times a gene hitting it')
        for row in genome_bin.itertuples():
            bin = getattr(row,'genome_bin')
            number = getattr(row, 'times_gene_hit')
            summary.append(' '*35 +str(bin)+' '*10+str(number))

        with safeout(out+'/genome_bin.tsv', 'wt') as ofile:
            ofile.write('# Genome_bin from GMGC-Finder v{}\n'.format(__version__))
            genome_bin.to_csv(ofile, sep='\t', index=False)

        with safeout(out+'/hit_table.tsv', 'wt') as ofile:
            ofile.write('# Results from GMGC-Finder v{}\n'.format(__version__))
            hit_table.to_csv(ofile, sep='\t', index=False)

        with safeout(out+'/summary.txt', 'wt') as ofile:
            for s in summary:
                print(s)
                ofile.write(s+'\n')


        output_content = resource_string('gmgc_finder', 'output.md')
        with safeout(out+'/README.md', 'wt') as ofile:
                ofile.write(bytes.decode(output_content))

        end = datetime.datetime.now()

        run_metadata = {}

        run_metadata['Command_line'] = command_line
        run_metadata['GMGC-Finder'] = __version__
        run_metadata['Start time'] = str(start)
        run_metadata['End time'] = str(end)
        run_metadata['Run time'] = (end-start).seconds
        run_metadata['Inputs'] = []

        if args.genome_fasta is not None:
            run_metadata['Inputs'].append(
                    {'genome_input': input_metadata(args.genome_fasta) })
        if args.nt_input is not None:
            run_metadata['Inputs'].append(
                    {'nt_input': input_metadata(args.nt_input)})
        if args.aa_input is not None:
            run_metadata['Inputs'].append(
                    {'aa_input': input_metadata(args.aa_input)})

        with safeout(out+'/runlog.yaml', 'wt') as ofile:
            yaml.dump(run_metadata, ofile, default_flow_style=False)


if __name__ == '__main__':
    main(sys.argv)

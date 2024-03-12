import random

simulate_deletion_lens = range(30) #deletions to simulate - here, 0 to 30bp deletions. The longer the deletion, the more adapter will be included in the read
simulate_mismatch_counts = range(3) #number of mismatches to simulate - her, 0, 1, and 2 mismatches between r1 and r2. The higher the number of mismatches, the less likely the read will be merged.
read_len = 210 #length of reads to generate

read        = '                                 CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG                                 '
readthrough = 'ACACTCTTTCCCTACACGACGCTCTTCCGATCTCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGGAGATCGGAAGAGCACACGTCTGAACTCCAGTCA'


complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
nucleotides = list(complement.keys())

def rev_comp(seq):
    bases = list(seq)
    bases = [complement[base] for base in bases]
    return ''.join(bases[::-1])

start_spaces = 0
for i in range(len(read)):
    if read[i] == ' ':
        start_spaces += 1
    else:
        break

end_spaces = 0
for i in range(len(read)-1,0,-1):
    if read[i] == ' ':
        end_spaces += 1
    else:
        break

indel_loc = 80 + start_spaces

print(f"5' adapter length: {start_spaces}")
print(f"3' adapter length: {end_spaces}")

end_loc = len(readthrough)-end_spaces

#with 210 read length, any more than 13bp deletion will result in adapter readthrough
max_indel_no_adapter = len(read.replace(' ','')) - read_len
print(f'Only reads with deletions longer than {max_indel_no_adapter}bp will have adapter readthrough')

print('Starting simulation')
file_root = 'makeSims.py.read_length_'+str(read_len)
read_id = 0
with open(file_root+".r1.fq",'w') as f1out, open(file_root+".r2.fq",'w') as f2out:
    for indel_len in simulate_deletion_lens:
        for num_mismatches in simulate_mismatch_counts:
            readthrough_copy = readthrough[0:indel_loc] + readthrough[indel_loc+indel_len:]
            copy_end_loc = len(readthrough_copy)-end_spaces
            sim_read1 = readthrough_copy[start_spaces:start_spaces+read_len]

            sim_read2 = readthrough_copy[copy_end_loc-read_len:copy_end_loc]
            sim_read2 = rev_comp(sim_read2)
            sub_locs = random.sample(range(len(sim_read2)),num_mismatches)
            for sub_loc in sub_locs:
                sim_read2 = sim_read2[0:sub_loc]+complement[sim_read2[sub_loc]] + sim_read2[sub_loc+1:]

            expected_adapter_len = max(0,indel_len-max_indel_no_adapter) #how much adapter will be at the end of the read
            this_id = f'@sim_read_{read_id}__indel_len_{indel_len}__expected_adapter_{expected_adapter_len}__sub_locs_'+','.join([str(x) for x in sub_locs])
            this_qual = 'A'*len(sim_read1)
            f1out.write(f'{this_id}\n{sim_read1}\n+\n{this_qual}\n')
            f2out.write(f'{this_id}\n{sim_read2}\n+\n{this_qual}\n')
            read_id += 1
print(f'Finished. Printed {read_id} simulations.')


print('Writing single-end file with trimming required')
read_id = 0
with open(file_root+".single_end_trim_reqd.r1.fq",'w') as f1out:
    for i in range(100):
        random_bases = ''.join(random.choices(nucleotides,k=5))
        sim_read1 = readthrough[start_spaces:] + random_bases
        this_id = f'@sim_read_{read_id}'
        this_qual = 'H'*len(sim_read1)
        f1out.write(f'{this_id}\n{sim_read1}\n+\n{this_qual}\n')
        read_id += 1
print('Finished')

print('Writing paired-end file with trimming required')
read_id = 0
with open(file_root+".paired_end_trim_reqd.r1.fq",'w') as f1out, open(file_root+".paired_end_trim_reqd.r2.fq",'w') as f2out:
    for i in range(100):
        random_bases = ''.join(random.choices(nucleotides,k=5))
        sim_read1 = readthrough[start_spaces:] + random_bases
        copy_end_loc = len(readthrough)-end_spaces
        sim_read2 = readthrough[0:copy_end_loc]
        random_bases = ''.join(random.choices(nucleotides,k=5))
        sim_read2 = rev_comp(sim_read2) + random_bases
        this_id = f'@sim_read_{read_id}'
        this_qual = 'H'*len(sim_read1)
        f1out.write(f'{this_id}\n{sim_read1}\n+\n{this_qual}\n')
        f2out.write(f'{this_id}\n{sim_read2}\n+\n{this_qual}\n')
        read_id += 1
print('Finished')


print('Writing paired-end file with merging required')
read_id = 0
with open(file_root+".paired_end_merge_reqd.r1.fq",'w') as f1out, open(file_root+".paired_end_merge_reqd.r2.fq",'w') as f2out:
    for i in range(100):
        sim_read1 = readthrough[start_spaces:start_spaces+read_len]

        copy_end_loc = len(readthrough)-end_spaces
        sim_read2 = readthrough[copy_end_loc-read_len:copy_end_loc]
        sim_read2 = rev_comp(sim_read2)

        this_id = f'@sim_read_{read_id}'
        this_qual = 'H'*len(sim_read1)
        f1out.write(f'{this_id}\n{sim_read1}\n+\n{this_qual}\n')
        f2out.write(f'{this_id}\n{sim_read2}\n+\n{this_qual}\n')
        read_id += 1
print('Finished')

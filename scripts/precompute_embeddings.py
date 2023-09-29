import hydra 
from omegaconf import DictConfig, OmegaConf
import torch
import os
import bend.io.sequtils as sequtils
import pandas as pd
from bioio.tf import dataset_from_iterable
#from bioio.tf import dataset_to_tfrecord
from bend.io.datasets import dataset_to_tfrecord
import sys
# load config 
@hydra.main(config_path="../conf/embedding/", config_name="embed", version_base=None)
def run_experiment(cfg: DictConfig) -> None:
    """
    Run a embedding of nucleotide sequences.
    This function is called by hydra.
    Parameters
    ----------
    cfg : DictConfig
        Hydra configuration object.
    """
    print('Embedding data for', cfg.task)
    # read the bed file and get the splits :  
    if not 'splits' in cfg or cfg.splits is None:
        splits = sequtils.get_splits(cfg[cfg.task].bed) 
    else:
        splits = cfg.splits
    print('Embedding with', cfg.model) 
    # instatiante model
    embedder = hydra.utils.instantiate(cfg[cfg.model])
    for split in splits:
        print(f'Embedding {split} set')
        output_dir = f'{cfg.data_dir}/{cfg.task}/{cfg.model}/'
        
        os.makedirs(output_dir, exist_ok=True)

        # embed in chunks 
        # get length of bed file and divide by chunk size, if a spcific chunk is not set 
        df = pd.read_csv(cfg[cfg.task].bed, sep = '\t')
        df = df[df.iloc[:, -1] == split] if split is not None else df
        possible_chunks = list(range(int(len(df) /cfg.chunk_size)+1))
        if cfg.chunk is None: 
            cfg.chunk = possible_chunks
        else:
            chunks_ok = []
            for chunk in cfg.chunk:
                if chunk in possible_chunks:
                    chunks_ok.append(chunk)
                else:
                    print(f'Skipping impossible chunk {chunk}')
                    # raise ValueError(f'Requested chunk {chunk}, but chunk ids range from {min(possible_chunks)}-{max(possible_chunks)}')
            
        # embed in chunks
        for chunk in chunks_ok: 
            print(f'Embedding chunk {chunk}/{len(possible_chunks)}')
            gen = sequtils.embed_from_bed(**cfg[cfg.task], embedder = embedder, split = split, chunk = chunk, chunk_size = cfg.chunk_size,   
                                        upsample_embeddings = cfg[cfg.model]['upsample_embeddings'] if 'upsample_embeddings' in cfg[cfg.model] else False)
            # save the embeddings to tfrecords 
            dataset = dataset_from_iterable(gen)
            dataset.element_spec
            dataset_to_tfrecord(dataset, f'{output_dir}/{split}_{chunk}.tfrecord')
        



if __name__ == '__main__':
    
    print('Run Embedding')
    
    run_experiment()
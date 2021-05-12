import os
import random

import torch

from FastSpeech2.FastSpeech2 import FastSpeech2
from FastSpeech2.FastSpeechDataset import FastSpeechDataset
from FastSpeech2.fastspeech2_train_loop import train_loop
from TransformerTTS.TransformerTTS import Transformer
from Utility.path_to_transcript_dicts import build_path_to_transcript_dict_libritts as build_path_to_transcript_dict


def run(gpu_id, resume_checkpoint, finetune, model_dir):
    if gpu_id == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        device = torch.device("cpu")

    else:
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "{}".format(gpu_id)
        device = torch.device("cuda")

    torch.manual_seed(13)
    random.seed(13)

    print("Preparing")
    cache_dir = os.path.join("Corpora", "LibriTTS")
    if model_dir is not None:
        save_dir = model_dir
    else:
        save_dir = os.path.join("Models", "FastSpeech2_LibriTTS")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    path_to_transcript_dict = build_path_to_transcript_dict()

    acoustic_model = Transformer(idim=165, odim=80, spk_embed_dim=256)
    acoustic_model.load_state_dict(torch.load(os.path.join("Models", "TransformerTTS_LibriTTS", "best.pt"),
                                              map_location='cpu')["model"])

    train_set = FastSpeechDataset(path_to_transcript_dict,
                                  cache_dir=cache_dir,
                                  acoustic_model=acoustic_model,
                                  lang="en",
                                  min_len_in_seconds=1,
                                  max_len_in_seconds=10,
                                  device=device,
                                  speaker_embedding=True,
                                  diagonal_attention_head_id=16)

    model = FastSpeech2(idim=165, odim=80, spk_embed_dim=256)

    print("Training model")
    train_loop(net=model,
               train_dataset=train_set,
               device=device,
               save_directory=save_dir,
               steps=400000,
               batch_size=32,
               gradient_accumulation=1,
               epochs_per_save=10,
               use_speaker_embedding=True,
               lang="en",
               lr=0.001,
               warmup_steps=8000,
               path_to_checkpoint=resume_checkpoint,
               fine_tune=finetune)

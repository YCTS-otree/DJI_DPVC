# -*- coding: utf-8 -*-
from datetime import datetime
import json
import re
import ffmpeg
import os

root_path = os.path.split(os.path.realpath(__file__))[0] + '\\'

# 读取配置文件
with open(root_path + 'config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

resolution = config['resolution']              # 输出视频分辨率
frame_rate = config['frame_rate']              # 输出视频帧率
bit_rate = config['output_bit_rate']           # 输出视频码率
black_bit_rate = config['black_output_bit_rate']  # 纯黑视频码率
codec = config['codec']                        # 编解码器
set_start_index = config['index']              # 起始序号
use_crf = config.get('use_crf', False)         # 是否启用CRF
crf_quality = config.get('crf_quality', 23)    # CRF质量等级

def encode_v1(input_path, output_path, filename, gpu=True):
    global codec

    input_video = input_path
    output_video = output_path + '\\' + filename + '.LRF.mp4'
    black_video = output_path + '\\' + filename + '.MP4'
    gpu_acceleration = gpu

    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    if gpu_acceleration:
        if codec == 'libx265':
            codec = 'hevc_nvenc'
        elif codec == 'libx264':
            codec = 'h264_nvenc'

    ffmpeg_args = {
        's': resolution,
        'r': frame_rate,
        'c:v': codec,
        'b:v': bit_rate
    }

    if use_crf:
        ffmpeg_args['crf'] = crf_quality
    else:
        ffmpeg_args['b:v'] = bit_rate

    ffmpeg.input(input_video).output(output_video, **ffmpeg_args).run()

    probe = ffmpeg.probe(output_video)
    video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    input_width = video_stream['width']
    input_height = video_stream['height']
    input_duration = float(video_stream['duration'])

    ffmpeg.input(
        f'color=c=black:s={input_width}x{input_height}:d={input_duration}',
        f='lavfi',
        r=frame_rate
    ).output(
        black_video,
        **{
            'b:v': black_bit_rate,
            'c:v': codec
        }
    ).run()

def get_max_index_from_files(directory):
    pattern = re.compile(r'_D\.MP4', re.IGNORECASE)
    indices = []

    for filename in os.listdir(directory):
        if pattern.match(filename):
            index = int(filename.split('_')[2])
            indices.append(index)

    if indices:
        return max(indices) + 1
    else:
        return 1

def Automatic_sorting_execution(Camera_directory, input_directory, output_path, input_file_list=None, start_index=None):
    if start_index is None or start_index == '':
        start_index = get_max_index_from_files(Camera_directory)
    else:
        start_index = int(start_index)

    if input_file_list is None:
        video_paths = [os.path.join(input_directory, f) for f in os.listdir(input_directory) if f.lower().endswith('.mp4')]
    else:
        video_paths = [f for f in input_file_list if f.endswith('.mp4')]

    video_paths.sort()

    for i, path in enumerate(video_paths):
        filename = os.path.basename(path)
        new_index = f'{start_index + i:04d}'
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f'DJI_{current_time}_{new_index}_D'

        encode_v1(input_path=path, output_path=output_path, filename=new_filename, gpu=True)

        folder_path = output_path
        for filepath in [os.path.join(output_path, f) for f in os.listdir(output_path) if f.lower().endswith('.lrf.mp4')]:
            filename = os.path.basename(filepath)
            new_filename = filename[:-4]
            new_filepath = os.path.join(folder_path, new_filename)
            os.rename(filepath, new_filepath)

Cam_directory = 'D:\\Action4视频放置\\output'
in_directory = config['v_input_path']
output_path = config['v_output_path']

Automatic_sorting_execution(Cam_directory, in_directory, output_path, start_index=set_start_index)

print("视频压缩和黑屏视频创建完成")

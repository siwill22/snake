import os
import numpy as np
import moviepy.editor as mpy



def get_jpeg_files(folder_path):
    jpeg_files = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.jpeg') or filename.lower().endswith('.jpg'):
            if float(filename.split('_')[1].split('.')[0])<1991.:
                jpeg_files.append('{:s}/{:s}'.format(folder_path,filename))
    jpeg_files.sort()  # Sort the list of JPEG files in ascending order
    return jpeg_files

folder_path = './sequence/Shiptracks/'
frame_list = get_jpeg_files(folder_path)


clip = mpy.ImageSequenceClip(frame_list[5000:-1], fps=20)

#clip.resize(0.5)

#clip.write_gif('./Shiptracks_1960_1990.gif')
clip.write_videofile('./Shiptracks_test.mp4')

import h5py
import hdf5plugin
import numpy as np
import argparse
import fabio
def get_format(file_path: str) -> str:
    ext=(file_path.split("/")[-1]).split(".")[-1]
    filt_ext=""
    for i in ext:
        if i.isalpha():
            filt_ext+=i
    return str(filt_ext)

def main():
    parser=argparse.ArgumentParser(
        description="Merge summed up PILATUS images.")
    parser.add_argument("-i", "--input", type=str, action="store",
        help="path to H5 data files")
    parser.add_argument("-n", "--n_frames", default=None, type=int, action="store",
        help="number of frames to sum")
    parser.add_argument("-o", "--output", type=str, action="store",
        help="path to H5 data files")
    args = parser.parse_args()

    files=open(args.input,'r')
    paths=files.readlines()

    count=0
    data=[]
    
    for idx,i in enumerate(paths[:args.n_frames]):
        file_format=get_format(i)
        if file_format=='cbf':
            frame = np.array(fabio.open(f"{i[:-1]}").data)
            data.append(frame)
            
        elif file_format=='h5':
            hdf5_file=str(i[:-1])
            f = h5py.File(hdf5_file,'r')
            print(f.keys())
            data.append(np.array(f['entry/data/data'][idx]))
        
        if count==0:
           acc=np.zeros((data[0].shape))
        count+=1

    for j in data:
        acc+=j
              
    g=h5py.File(args.output,'w')
    g.create_dataset('data', data=acc)
    g.close()

if __name__ == '__main__':
    main()

import numpy as np
from dataclasses import dataclass, field
import subprocess as sub
import math
from om.algorithms.crystallography import TypePeakList, Peakfinder8PeakDetection


def build_pixel_map(row: int, col: int, y0: int, x0: int):
    radius_pixel_map = np.ones((row, col)).astype(int)
    for idy, i in enumerate(radius_pixel_map):
        for idx, j in enumerate(i):
            radius_pixel_map[idy, idx] = int(
                math.sqrt((idx - x0) ** 2 + (idy - y0) ** 2)
            )
    return dict(radius=radius_pixel_map)


@dataclass
class PF8Info:
    max_num_peaks: int
    pf8_detector_info: dict
    adc_threshold: float
    minimum_snr: int
    min_pixel_count: int
    max_pixel_count: int
    local_bg_radius: int
    min_res: float
    max_res: float
    _bad_pixel_map: np.array
    _pixelmaps: np.array = field(init=False)

    def __post_init__(self):
        print(self._bad_pixel_map.shape)
        self._pixelmaps = build_pixel_map(
            (self._bad_pixel_map).shape[0],
            (self._bad_pixel_map.shape[1]),
            int((self._bad_pixel_map).shape[0] / 2),
            int((self._bad_pixel_map).shape[1] / 2),
        )

    def copy_and_modify_mask(self, mask):
        pf8_info_modified = PF8Info(
            max_num_peaks=self.max_num_peaks,
            pf8_detector_info=self.pf8_detector_info,
            adc_threshold=self.adc_threshold,
            minimum_snr=self.minimum_snr,
            min_pixel_count=self.min_pixel_count,
            max_pixel_count=self.max_pixel_count,
            local_bg_radius=self.local_bg_radius,
            min_res=self.min_res,
            max_res=self.max_res,
            _bad_pixel_map=mask,
        )
        return pf8_info_modified

    def modify_radius(self, center_x, center_y):
        self._pixelmaps = build_pixel_map(
            (self._bad_pixel_map).shape[0],
            (self._bad_pixel_map.shape[1]),
            center_y,
            center_x,
        )


"""
class PF8:
    ### call pf8 from indexamajig
    def __init__(self, info):
        assert isinstance(info, PF8Info), f"Info object expected type PF8Info, found {type(info)}."
        self.pf8_param = info

    def get_peaks_pf8(self, data, stream, geom):

        max_num_peaks=self.pf8_param.max_num_peaks,
        bad_pixel_map=self.pf8_param._bad_pixel_map,
        radius_pixel_map=self.pf8_param._pixelmaps["radius"],
        asic_nx=self.pf8_param.pf8_detector_info["asic_nx"],
        asic_ny=self.pf8_param.pf8_detector_info["asic_ny"],
        nasics_x=self.pf8_param.pf8_detector_info["nasics_x"],
        nasics_y=self.pf8_param.pf8_detector_info["nasics_y"],
        adc_threshold=self.pf8_param.adc_threshold,
        minimum_snr=self.pf8_param.minimum_snr,
        min_pixel_count=self.pf8_param.min_pixel_count,
        max_pixel_count=self.pf8_param.max_pixel_count,
        local_bg_radius=self.pf8_param.local_bg_radius,
        min_res=self.pf8_param.min_res,
        max_res=self.pf8_param.max_res
        
        cmd = f"indexamajig -i {data} -o {stream} -g {geom} --peaks=peakfinder8 --indexing=none --threshold={self.pf8_param.adc_threshold} --min-snr={self.pf8_param.minimum_snr} --min-pix-count={self.pf8_param.min_pixel_count} --max-pix-count={self.pf8_param.max_pixel_count} --min-res={self.pf8_param.min_res} --max-res={self.pf8_param.max_res} --local-bg-radius={self.pf8_param.local_bg_radius}"
        print(cmd)
        sub.call(cmd,shell=True)
        cmd=f"grep num_peaks {stream}> tmp"

        sub.call(cmd,shell=True)
        f=open("tmp", "r")
        lines=f.readlines()
        f.close()
        n_peaks=[]
        for i in lines:
            n_peaks.append(int(i.split("=")[-1]))
        print(n_peaks)
        peak_list=[]
        for i in n_peaks:
            cmd=f"grep 'Peaks from peak search' -A {i+1} {stream}> tmp"
            sub.call(cmd,shell=True)
            f=open("tmp", "r")
            lines=f.readlines()
            f.close()
            peak_list={"fs/px": [], "ss/px": []}
            
            for j in lines[2:]:
                cols=j.split(".")
                peak_list["fs/px"].append(int(cols[0]))
                peak_list["ss/px"].append(int(cols[1].split(" ")[-1]))
            
        return peak_list
        
"""


class PF8:
    ##test for om peakfinder8
    def __init__(self, info):
        assert isinstance(
            info, PF8Info
        ), f"Info object expected type PF8Info, found {type(info)}."
        self.pf8_param = info

    def get_peaks_pf8(self, data):
        detector_layout = self.pf8_param.pf8_detector_info
        print(detector_layout)
        peak_detection = Peakfinder8PeakDetection(
            self.pf8_param.max_num_peaks,
            self.pf8_param.pf8_detector_info["asic_nx"],
            self.pf8_param.pf8_detector_info["asic_ny"],
            self.pf8_param.pf8_detector_info["nasics_x"],
            self.pf8_param.pf8_detector_info["nasics_y"],
            self.pf8_param.adc_threshold,
            self.pf8_param.minimum_snr,
            self.pf8_param.min_pixel_count,
            self.pf8_param.max_pixel_count,
            self.pf8_param.local_bg_radius,
            self.pf8_param.min_res,
            self.pf8_param.max_res,
            self.pf8_param._bad_pixel_map.astype(np.float32),
            (self.pf8_param._pixelmaps["radius"]).astype(np.float32),
        )
        peaks_list = peak_detection.find_peaks(data)
        return peaks_list

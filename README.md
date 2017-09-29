# Gravitational_Wave_Analysis
Analyze gravitational-wave data, find signals, and study their parameters. 
Pulls strain data from the two logo detectors for 100% quality data files for the S6 data release. 
Portions of the code are from LIGO's binary at https://github.com/ligo-cbc/pycbc. 
Program differs from LIGO's in that it searches for matching wave characters rather than filtering data with known wavelengths

# This program uses OSX-terminal specific commands. 
If using another operating system, run the program in an OSX-terminal emulator

# Requires h5dump version 1.8.16 or newer
h5dump is included in the HDFView package available at https://support.hdfgroup.org/downloads/index.html

# Running the program
In terminal:
> python ligo_view  

downloads, reads, and analyzes strain data for the first H1 and L1 detector data associated with the first
file in list.txt
                     
> python ligo_view -i 0 -f 5  

downloads, reads, and analyzes strain data for the first six H1 and L1 detector data associated with
first six files in list.txt
                               
                               
# Program Output
The program saves a whitened png file containing superposed data from both detectors.
If a gravitational wave candidate is found, the program saves an additional png file, zoomed in on the location of the candidate.

Note, the full anaysis takes about 5 minutes per pair of Ligo data files, due to the size and number of data points

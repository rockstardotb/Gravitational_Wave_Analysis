# Standard python numerical analysis imports:
from scipy import signal
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt, iirdesign, zpk2tf, freqz

# Plotting imports
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np

# Terminal CMD utility imports
import os
import sys
import argparse

# import allows download of strain data from ligo database
import urllib.request

# The following three variables are for tweaking the chi_square (goodness of fit) search parameters.
c=32	#This effects the span for which index values much match the chi_threshold
	#i.e., strain_H1_whitenbp[i-c:i+c]
chi_interval=c/4	#The program moves the search forward by c/2 index so that
			#there is overlap and nothing is missed
chi_threshold=0.45      #Anything below this threshold is zoomed in on and saved


# Allow command-line search parameter input
parser = argparse.ArgumentParser() 
parser.add_argument('-i',    default=0,    help='starting index of list of 100% data files')
parser.add_argument('-f',    default=1,    help='ending index of list of 100% data files')
args=parser.parse_args()
I=args.i
F=args.f

# read list of Ligo filenames into array
list=[]
with open('list.txt','r') as f:
	array=np.loadtxt(f,dtype=int)
list=array[int(I):int(F)]

index=I
b=931135488
for row in list:		
	
	file_nameH1="H-H1_LOSC_4_V1-"+str(row)+"-4096.hdf5"
	file_nameL1="L-L1_LOSC_4_V1-"+str(row)+"-4096.hdf5"

	# URL naming convention changes every 1048576 seconds in filename
	while row>b+1048576:
		b+=1048576

	# download hdf5 files from ligo
	urlL1="https://losc.ligo.org/archive/data/S6/"+str(b)+"/L-L1_LOSC_4_V1-"+str(row)+"-4096.hdf5"
	urlH1="https://losc.ligo.org/archive/data/S6/"+str(b)+"/H-H1_LOSC_4_V1-"+str(row)+"-4096.hdf5"
	urllib.request.urlretrieve(urlL1, file_nameL1)
	urllib.request.urlretrieve(urlH1, file_nameH1)

	# convert hdf5 to text
	os.system("h5dump -d /strain/Strain -y -w 1 -o "+file_nameH1+".txt "+file_nameH1)
	os.system("h5dump -d /strain/Strain -y -w 1 -o "+file_nameL1+".txt "+file_nameL1)
	timeH1=[]
	timeL1 = []
	comma_strainH1=[]
	comma_strainL1=[]
	strainH1 = []
	strainL1 = []

	# read text files into arrays
	def readH1():
		global H1,time,strainH1
		plt.rcParams['agg.path.chunksize'] = 10000

		i=0
		with open(file_nameH1+".txt", 'r') as f:
			for row in f:
				if row==' ':
					# skip blank spaces in beginning of text files
					continue
				else:
					comma_strainH1.append(row.strip())
			filter(None, comma_strainH1)

		# remove text file created by HDFView
		os.system("rm "+file_nameH1+".txt")	


		# This portion only applies to data files rated as less than 100% by ligo
		# All data files listed in list.txt are 100%
		##########################################################
		for row in comma_strainH1:
			if row=="NaN":
				i+=1
			elif row=="":
				continue
			else:
				timeH1.append(float(0.00024414063955*i))
				strainH1.append(float(row.strip(',')))
				i+=1
		###########################################################
	#	plt.plot(timeH1,strainH1)   # UnComment to see unfiltered plots
	#	plt.clf()
		return timeH1
		return strainH1
	def readL1():
		global L1,time,strainL1
		plt.rcParams['agg.path.chunksize'] = 10000

		i=0

		with open(file_nameL1+".txt", 'r') as f:
			for row in f:
				comma_strainL1.append(row.strip())
			filter(None, comma_strainL1)
		os.system("rm "+file_nameL1+".txt")
		for row in comma_strainL1:
			if row=="NaN":
				i+=1
			elif row=="":
				continue
			else:
				timeL1.append(float(0.00024414063955*i))
				strainL1.append(float(row.strip(',')))
				i+=1
	#       plt.plot(timeL1,strainL1)  # UnComment to see unfiltered plot
	#	plt.clf()	
		return timeL1
		return strainL1
	os.system("rm "+file_nameH1)
	os.system("rm "+file_nameL1)
	readH1()
	readL1()
	#plt.savefig('raw'+H1+'.png') # UnComment to save png of unfiltered plot
	#plt.show()

	#########################################################################
	#########################  Begin LIGO binary ############################
	#########################################################################

	fs= 4096 # number of seconds in sample
	dt=timeH1[1]-timeH1[0]
	# number of sample for the fast fourier transform:
	NFFT = 1*fs
	fmin = 10
	fmax = 2000
	Pxx_H1, freqs = mlab.psd(strainH1, Fs=fs, NFFT=NFFT)
	Pxx_L1, freqs = mlab.psd(strainL1, Fs = fs, NFFT = NFFT)
	# We will use interpolations of the ASDs computed above for whitening:
	# Below, data less than zero is being created in the array psd_H1.
	# Consider writing a loop to change values less than zero to zero.
	psd_H1 = interp1d(freqs, Pxx_H1,copy= True,bounds_error=False,fill_value=0.1*10**(-75))
	psd_L1 = interp1d(freqs, Pxx_L1,copy= True,bounds_error=False,fill_value=0.1*10**(-75))
	
	# UnComment code below to see whitened plots
	# plot the ASDs:
	#plt.figure()
	#plt.loglog(freqs, np.sqrt(Pxx_H1),'r',label='H1 strain')
	#plt.loglog(freqs, np.sqrt(Pxx_L1),'g',label='L1 strain')
	#plt.axis([fmin, fmax, 1e-24, 1e-19])
	#plt.grid('on')
	#plt.ylabel('ASD (strain/rtHz)')
	#plt.xlabel('Freq (Hz)')
	#plt.legend(loc='upper center')
	#plt.title('Advanced LIGO strain data')
	#plt.savefig('New_ASDs'+H1+'.png')
	#plt.show()
	#plt.clf()
	
	
	# function to writen data
	def whiten(strain, interp_psd, dt):
	    Nt = len(strain)
	    freqs = np.fft.rfftfreq(Nt, dt)
	
	    # whitening: transform to freq domain, divide by asd, then transform back,
	    # taking care to get normalization right.
	    hf = np.fft.rfft(strain)
	    #**********************************************************#
	    white_hf = hf / (np.sqrt(interp_psd(freqs)/dt/2.))
	    white_ht = np.fft.irfft(white_hf, n=Nt)
	    return white_ht
	    #***********************************************************#
	    white_hf = hf / (np.sqrt(interp_psd(freqs) /dt/2.))
	    white_ht = np.fft.irfft(white_hf, n=Nt)
	    return white_ht
	
	# now whiten the data from H1 and L1, and also the NR template:
	strain_H1_whiten = whiten(strainH1,psd_H1,dt)
	strain_L1_whiten = whiten(strainL1,psd_L1,dt)
	#NR_H1_whiten = whiten(NR_H1,psd_H1,dt)
	
	# We need to suppress the high frequencies with some bandpassing:
	bb, ab = butter(4, [10.0*2/fs,300*2/fs], btype='band') # fiddle with numbers instead of '16'
	strain_H1_whitenbp = filtfilt(bb, ab, strain_H1_whiten)
	strain_L1_whitenbp = filtfilt(bb, ab, strain_L1_whiten)
	#NR_H1_whitenbp = filtfilt(bb, ab, NR_H1_whiten)
	# plot the data after whitening:
	# first, shift L1 by 7 ms, and invert. See the GW150914 detection paper for why!
	strain_L1_shift = -np.roll(strain_L1_whitenbp,int(0.007*fs))
	
	plt.plot(timeH1,strain_H1_whitenbp,'r',label='H1 strain')
	plt.plot(timeL1,strain_L1_shift,'g',label='L1 strain')
	#plt.plot(NRtime+0.002,NR_H1_whitenbp,'k',label='matched NR waveform')
	if np.sum(timeH1)<=2100000:
		plt.xlim([0,32])
	else:
		plt.xlim([0,4096])
	plt.ylim([-4,4])
	plt.xlabel('time (s)')
	plt.ylabel('whitented strain')
	plt.legend(loc='lower left')
	plt.title('Advanced LIGO WHITENED strain data')
	plt.savefig('NEW_strain_whitened'+file_nameH1+'.png')
#	plt.show()
	plt.clf()
	time_start=0
	time_end=0

        #########################################################################
        #########################  End LIGO binary ############################
        #########################################################################

	# Search through 32 second data for spikes
	if np.sum(timeH1)<=2100000:
		# Index starts where the skipped section ends
		index=1000
		# Skips the first and last segment of data since it is just noise
		for x,y,x1,y1 in zip(timeH1[1000:120000],strain_H1_whitenbp[1000:120000],timeL1[1000:120000],strain_L1_shift[1000:120000]):
			# Threshold is set here
			if y>1.75 and y1>1.75:
				print('H1: (',x,',',y,')\tL1:(',x1,',',y1,')')
				# This is the start time for the zoomed in plot
				if time_start==0:
					time_start=index-100
				time_end=index+100
				index+=1
			else:
				index+=1
				continue
		#calculate chi-squared of spikes
		if time_end>time_start:
			t_list=[]
			chi_list=[]
			chi=0.0
			chit1=0.0
			chit2=0.0
			chit3=0.0
			chit_1=0.0
			chit_2=0.0
			chit_3=0.0
			def chi_32(t):
				chit=0.0
				y=strain_H1_whitenbp[time_start+80+t:time_end-100+t]
				y1=strain_L1_shift[time_start+80+t:time_end-100+t]
				for a,b in zip(y,y1):
					chit+=abs(((a-b)**2))
				return chit
			t=0
			chi=chi_32(t)
			t=1
			chit1=chi_32(t)
			t=2
			chit2=chi_32(t)
			t=3
			chit3=chi_32(t)
			t=-1
			chit_1=chi_32(t)
			t=-2
			chit_2=chi_32(t)
			t=-3
			chit_3=chi_32(t)
			t_list=[-3*0.00024414063955+0.007,-2*0.00024414063955+0.007,-1*0.00024414063955+0.007,0*0.00024414063955+0.007,1*0.00024414063955+0.007,2*0.00024414063955+0.007,3*0.00024414063955+0.007]
			chi_list=[chit_3,chit_2,chit_1,chi,chit1,chit2,chit3]
			plt.plot(t_list,chi_list, 'ro')
			plt.xlabel('time shift (s)')
			plt.ylabel('Chi Squared')
			plt.title('Chi Squared vs Time Shift')
			plt.savefig('chiVStshift'+file_nameH1+'.png')
			plt.clf()
		else:
			continue
		#Search through noise using chi-squared analysis
		i=1000
		y2=[]
		y3=[]
		while i<120000:
			chi1=0
			y2=strain_H1_whitenbp[i-int(c):i+int(c)]
			y3=strain_L1_shift[i-int(c):i+int(c)]
			for a,b in zip(y2,y3):
				chi1+=abs(((a-b)**2))
			if chi1>float(chi_threshold):
				i+=int(chi_interval)
				chi1=0
			else:
				plt.plot(timeH1[i-100:i+100],strain_H1_whitenbp[i-100:i+100],'r',label='H1 strain')
				plt.plot(timeL1[i-100:i+100],strain_L1_shift[i-100:i+100],'g',label='L1 strain')
				plt.ylim([-4,4])
				#plt.text(timeH1[i-50]+0.005,3,r'Approximate solar mass of final black hole: '+str(format(mass_approx,'0.1f')))
				plt.text(timeH1[i-100]+0.02,-3,r'chi-squared='+str(chi1))
				plt.xlabel('time (s)')
				plt.ylabel('whitented strain')
				plt.legend(loc='lower left')
				plt.title('Advanced LIGO WHITENED strain data: inside noise')
				plt.savefig('ZoomedNEW_IN_NOISE_strain_whitened'+file_nameH1+str(timeH1[i])+'.png')
				i+=2*int(c)+1
				chi1=0
				plt.clf()
	# This searches through the 4096 second data files
	else:
		# Index starts where the skipped section ends
		index=5000000
		# This skips the first and last segments of noise
		for x,y,x1,y1 in zip(timeH1[5000000:11000000],strain_H1_whitenbp[5000000:11000000],timeL1[5000000:11000000],strain_L1_shift[5000000:11000000]):
			# The threshold is set here			
			if y>1.5 and y1>1.5:
				# This is the start time for the zoomed in plot
				if time_start==0:
					time_start=index-100
				time_end=index+100
				index+=1
			else:
				index+=1
				continue
		#calculate chi-squared of spikes
		if time_end>time_start:
			t_list=[]
			chi_list=[]
			chi=0.0
			chit1=0.0
			chit2=0.0
			chit3=0.0
			chit_1=0.0
			chit_2=0.0
			chit_3=0.0
			def chi_32(t):
				chit=0.0
				y=strain_H1_whitenbp[time_start+80+t:time_end-100+t]
				y1=strain_L1_shift[time_start+80+t:time_end-100+t]
				for a,b in zip(y,y1):
					chit+=abs(((a-b)**2))
				return chit
			t=0
			chi=chi_32(t)
			t=1
			chit1=chi_32(t)
			t=2
			chit2=chi_32(t)
			t=3
			chit3=chi_32(t)
			t=-1
			chit_1=chi_32(t)
			t=-2
			chit_2=chi_32(t)
			t=-3
			chit_3=chi_32(t)
			t_list=[-3*0.00024414063955+0.007,-2*0.00024414063955+0.007,-1*0.00024414063955+0.007,0*0.00024414063955+0.007,1*0.00024414063955+0.007,2*0.00024414063955+0.007,3*0.00024414063955+0.007]
			chi_list=[chit_3,chit_2,chit_1,chi,chit1,chit2,chit3]
			plt.xlabel('time shift (s)')
			plt.ylabel('Chi Squared')
			plt.title('Chi Squared vs Time Shift')
			plt.plot(t_list,chi_list, 'ro')
			plt.savefig('chiVStshift'+file_nameH1+'.png')
			plt.clf()
		else:
			continue
		#search through noise with chi-squared analysis
		i=4999950
		y2=[]
		y3=[]
		while i<11000050:
			chi1=0
			y2=strain_H1_whitenbp[i-int(c):i+int(c)]
			y3=strain_L1_shift[i-int(c):i+int(c)]
			for a,b in zip(y2,y3):
				chi1+=abs(((a-b)**2))	
			if chi1>float(chi_threshold):
				i+=int(chi_interval)
				chi1=0
			else:
				plt.plot(timeH1[i-100:i+100],strain_H1_whitenbp[i-100:i+100],'r',label='H1 strain')
				plt.plot(timeL1[i-100:i+100],strain_L1_shift[i-100:i+100],'g',label='L1 strain')
				plt.ylim([-4,4])
				#plt.text(timeH1[i-100]+0.005,3,r'Approximate solar mass of final black hole: '+str(format(mass_approx,'0.1f')))
				plt.text(timeH1[i-100]+0.02,-3,r'chi-squared='+str(chi1))
				plt.xlabel('time (s)')
				plt.ylabel('whitented strain')
				plt.legend(loc='lower left')
				plt.title('Advanced LIGO WHITENED strain data: inside noise')
				plt.savefig('ZoomedNEW_IN_NOISE_strain_whitened'+file_nameH1+str(timeH1[i])+'.png')
				i+=2*int(c)+1
				chi1=0
				plt.clf()
	# Plot only if a spike above the specified threshold was found
	if time_end > time_start:
		maxH1=np.amax(strain_H1_whitenbp[time_start:time_end])
		maxL1=np.amax(strain_L1_shift[time_start:time_end])
		if np.amax(strain_H1_whitenbp)>4 or np.amax(strain_L1_shift):
#			strain_L1_shift = -np.roll(strain_L1_whitenbp,int(0.009*fs))
			plt.plot(timeH1,strain_H1_whitenbp,'r',label='H1 strain')
			plt.plot(timeL1,strain_L1_shift,'g',label='L1 strain')
			#plt.plot(NRtime+0.002,NR_H1_whitenbp,'k',label='matched NR waveform')
			plt.xlim((timeH1[time_start]),(timeH1[time_end]))
			# Distinguish bursts from merger candidates so code doesn't approximate mass
			if maxH1>4 or maxL1>4:
				print(-1*np.amax(strain_H1_whitenbp[time_start:time_end]))
				print(-np.amax(strain_L1_shift[time_start:time_end]))
				if maxH1>=maxL1:
					plt.ylim([(-1*maxH1)-1,(maxH1)+1])
					plt.text(timeH1[time_start]+0.03,(-1*maxH1),r'chi-squared='+str(format(chi,'0.2f')))
				if maxL1>maxH1:
					plt.ylim([(-1*maxL1)-1,(maxL1)+1])
					plt.text(timeH1[time_start]+0.03,(-1*maxL1),r'chi-squared='+str(format(chi,'0.2f')))
			# Approximate mass by using ratio of mass/period compared to mass/period for event
			else:
				zero_search=time_end-100
				while strain_H1_whitenbp[zero_search]>0:
					zero_search-=1
					zero1=zero_search
				zero_search=time_end-100
				while strain_H1_whitenbp[zero_search]>0:
					zero_search+=1
					zero2=zero_search
				period=((timeH1[zero2]-timeH1[zero1])*2)
				mass_approx=(62*period)/0.006
				plt.ylim([-4,4])
				plt.text(timeH1[time_start]+0.005,3,r'Approximate solar mass of final black hole: '+str(format(mass_approx,'0.1f')))
				plt.text(timeH1[time_start]+0.025,-3,r'chi-squared='+str(chi))
			plt.xlabel('time (s)')
			plt.ylabel('whitented strain')
			plt.legend(loc='lower left')
			plt.title('Advanced LIGO WHITENED strain data')
			plt.savefig('ZoomedNEW_strain_whitened'+file_nameH1+'.png')
	#		plt.show() # UnComment to see a plot. Plot will still be saved as png
		plt.clf()
	index+=1

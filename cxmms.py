#!/usr/bin/env python
#
# Copyright (C) 2005 Gopal Vijayaraghavan <gopalv82>
#
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; version 2 of the License.
#
# A Couple of More Features Added by Tejas Dinkar <tejasdinkar@gmail.com>
#
#  Cleanup of Code
#  Shuffle Funtion
#  Change Logging Style
#  Search Function
#  Fixed Bug regarding scroll bar
#  Include better song Searching
#
# And yes, it might not work for you ? :)

import xmms, curses
import select

debug = 0

def key_strokes():
	# This Corresponds to each Key Stroke's ASCII Value
	x = ord("x")
	c = ord("c")
	v = ord("v")
	z = ord("z")
	b = ord("b")
	j = ord("j")
	s = ord("s")
	esc = 0x1b
	up = 0x41
	down = 0x42
	right = 0x43
	left = 0x44
	enter = 0x0a
	backspace = 0x08
	return locals()

if debug:
	class logger:
		def __init__(self):
			self.log = open("/tmp/cxmms.log", "w")
		
		def write(self, str):
			self.log.write(str)
			self.log.flush()

	# Creates a Function called log
	log_file = logger()
	log = lambda a: log_file.write(a)
else:
	# This Sets Log File as /dev/null if needed
	log = lambda a: None

def format_time (time):
	if time > 3600:
		return "%02d:%02d:%02d" % (time/3600, (time % 3600)/60, time % 60)
	else:
		return "%02d:%02d" % (time/60,time % 60)

def logo(stdscr):
	str = ".::Commandline XMMS::."
	stdscr.insstr(3, 40-len(str)/2, str)
	stdscr.refresh()

	copyright = "(C) 2005, Blug.in"
	stdscr.insstr(20, 70-len(copyright), copyright)
	stdscr.refresh()
	

class xmms_main_window:
	def __init__(self, stdscr, top = 6,left = 10):
		self.stdscr = stdscr
		self.win = curses.newwin(13, 60, top, left)
		self.win.border()
		
		self.keys = key_strokes()

		self.timers = self.win.subwin(2, 10, top+1, left + 3)
		self.title = self.win.subwin(3, 40, top+1, left + 15)
		self.playtime = self.win.subwin(2, 40, top+4, left + 15)
		self.volume = self.win.subwin(7, 10, top+3, left + 2)
		self.jump = self.win.subwin(6, 45, top+6, left + 12)
		self.shuffle = self.win.subwin(1,1,top+10, left + 5)
		if xmms.is_shuffle():
			self.shuffle.insstr(0,0,"S")
			
		self.windows = [self.timers, self.playtime, self.shuffle, self.volume, self.win, self.jump, self.title]
		
		key = self.keys
		self.keymaps = {
			key["x"] : xmms.play,
			key["c"] : xmms.pause,
			key["v"] : xmms.stop,
			key["z"] : xmms.playlist_prev,
			key["b"] : xmms.playlist_next,
			key["s"] : self.toggle_shuffle,
			key["j"] : self.search,
			key["up"] : lambda : xmms.set_main_volume(min(100, xmms.get_main_volume() + 10)),
			key["down"] : lambda : xmms.set_main_volume(max(0, xmms.get_main_volume() - 10)),
			key["right"] : lambda : xmms.jump_to_time(xmms.get_output_time()+5000),
			key["left"] : lambda : xmms.jump_to_time(max(0,xmms.get_output_time()-5000))
		};

	def songs_that_match(self,string):
		songs = []
		for i in range(xmms.get_playlist_length()):
			if string.lower() in xmms.get_playlist_title(i).lower():
				songs.append(i)
		return songs
	
	def draw_jump(self,string):
		'''This Draws Jump.... But also returns next Songs Matching Query'''
		self.jump.clear()
		self.jump.insstr(1,2,"Search: %s" % string)
		songs = self.songs_that_match(string)
		i = 2
		for j in songs[:3]:
			if i == 2:
				style = curses.A_STANDOUT
			else:
				style = curses.A_NORMAL
			self.jump.insstr(i,2,xmms.get_playlist_title(j)[:42],style)
			i = i + 1
		self.jump.border()
		try: 
			return songs[0]
		except:
			return -1
	
	def search(self):
		self.jump.clear()
		string = ""
		# if any key pressed
		while True:
			song = self.draw_jump(string)
			self.update()
			# select() rocks, timeout == 1 sec
			(read, write, err) = select.select([0], [], [], 1)
			if 0 in read:
				key = self.win.getch()
				log("key pressed 0x%02x\n" % key)
				if key == self.keys["esc"]:
					self.jump.clear()
					return
				if key == self.keys["enter"]:
					if song != -1:
						xmms.set_playlist_pos(song)
						self.jump.clear()
						return
				if key == self.keys["backspace"]:
					string = string[:-1]
				else:
					string = string + chr(key)

	def toggle_shuffle(self):
		self.shuffle.clear()
		if xmms.is_shuffle():
			self.shuffle.insstr(0,0," ")
		else:
			self.shuffle.insstr(0,0,"S")
		xmms.toggle_shuffle()

	def update(self):
		time = xmms.get_output_time()/1000
		num = xmms.get_playlist_pos()
		title = xmms.get_playlist_title(num)
		shuffle = xmms.is_shuffle()
		length = xmms.get_playlist_time(num) / 1000
		
		t = format_time(time)
		self.timers.clear()
		self.timers.addstr(t)
		
		self.title.clear()
		self.title.addstr("%d. %s (%s)" % (num,title,format_time(length)))

		t = (time * 40) / length
		self.playtime.clear()
		self.playtime.insstr(0,0,'.' * t)
		self.playtime.insstr(0, min(t,39), '%',curses.A_BOLD)
		if t < 39:
			self.playtime.insstr(0,t+1,'.' * (39 -t))

		self.volume.clear()
		v = xmms.get_main_volume()
		self.volume.insstr(0,0, 'Vol: %2d' % (v))

		v = int(round(v / 10))
		for i in range(0, 5):
			if (i * 2 < v):
				self.volume.hline(6-i, 0, '#', 2*i-1, curses.A_BOLD)
			else:
				self.volume.hline(6-i, 0, '_', 2*i-1)
				
# 		# gratuitous use of lambda
		map(lambda a: a.refresh(), self.windows)
	
	def keyloop(self):
		quit = 0
		log("%s\n" % dir(self.timers))
		while not quit:
			self.update()
			# select() rocks, timeout == 1 sec
			(read, write, err) = select.select([0], [], [], 1)
			# if any key pressed
			if 0 in read:
				key = self.win.getch()
				if key == ord('q'):
					quit = 1
				else:
					log("key pressed 0x%02x\n" % key)
					if self.keymaps.has_key(key):
						self.keymaps[key]()

def main(stdscr):
	curses.savetty()
	try:
		logo(stdscr)
		w = xmms_main_window(stdscr)
		w.keyloop()
	finally:
		curses.resetty()

curses.wrapper(main)

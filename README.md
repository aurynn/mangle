# Mangle

### What

Mangle is a simple console-based program, designed to make it extremely easy for me to capture 
*what I'm currently doing*, as opposed to *what I need to do.*

Mangle grew out of a significant frustration with ticketing systems and to-do
programs; a lack of the state of Right Now.

Mangle uses Postgres as the backing store; I didn't want to rewrite sorting 
and querying technology just to write a tool.

Mangle is currently a single line.

### Usage

Mangle is used entirely from the shell. I generally use zshell, but anything 
should work.

First, alias mangle to something easily used:
<pre>
	$ alias am="python ~/src/mangle/mangle.py"
</pre>

Now, 
<pre>
	$ am doing "getting mangle onto github"
	$ am doing\?
	1: 2013-03-02 18:31:32.659763+13:00	getting mangle onto github
	$ am \?
	1: 2013-03-02 18:31:32.659763+13:00	getting mangle onto github
</pre>

capturing a task that I'm currently doing.

Next, I can log against an open "doing", via:
<pre>
	$ am did "wrote the readme"
	$ am did\?
	section: doing
	2013-03-02 18:38:37.653799+13:00:	wrote the readme
</pre>

The grammar isn't great, obviously.

Having multiple things in the doing queue also works:
<pre>
	$ am doing "argue on twitter"
	$ am \?
	1: 2013-03-02 18:47:02.112402+13:00	argue on twitter
	2: 2013-03-02 18:31:32.659763+13:00	Writing mangle readme
</pre>

Oh look, the ordering changed!

### Automatic Moving

So, Mangle intends to push things around automatically. Whatever you've last added, or last edited, is what gets used as 
the #1 slot in "doing".

This is because it is the mostly recently done thing, and new things should be the top of the list.

To address not the first, you do:

<pre>$ am did "talked about automatic moving" for 2</pre>

And it'll work as Expected.

## why

### isn't it in PyPI? 

Haven't gotten there yet.

### does it use Postgres?

Because I wanted it to be simple to query and work with the data later.

### use the shell?

Because I always have shells open; because it's the simplest way to just type some text, hit <Enter>, and save it out.
The fewer pieces that get into my way, the more likely I am do actually use it.

## Bugs

Report 'em! There's probably heaps!

## You hate it

That's okay! It's opinionated by design. It's going to be more so.
#!/usr/bin/python

import sys
import psycopg2
from psycopg2.extras import DictCursor

"""

CREATE TABLE sections (
    name TEXT NOT NULL PRIMARY KEY,
    description TEXT,
    created timestamptz NOT NULl DEFAULT NOW()
);

INSERT INTO sections (name, description) VALUES 
    ('doing',$$What you're doing$$), 
    ('not doing', $$What you're not doing.$$),
    ('backburner', $$Stuff that you're kinda-sorta-not-really doing.$$),
    ('limbo', 'Beyond backburner, the basis for this is no longer valid and may never be done'),
    ('ponies', 'Stuff you wish you could do.')
;

CREATE TABLE tasks (
    id SERIAL NOT NULL PRIMARY KEY,
    section TEXT NOT NULL REFERENCES sections(name),
    description TEXT NOT NULL,
    created timestamptz NOT NULL DEFAULT NOW(),
    done timestamptz,
    mu boolean default false
);

CREATE TABLE contents (
    task int not null references tasks(id),
    description text not null,
    created timestamptz not null default now()
);

create index task_is_not_done on tasks(done) where done is null;
create index task_is_done on tasks(done);

"""

sections = ["doing", "not doing", "backburner", "limbo", "ponies"]

def interval_(i):
    """
    Returns a callable that runs some DB stuff, I guess?
    """
    pass


def last_modified_task(conn):
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("""
                SELECT stuff.id FROM (
                    SELECT t.id,
                           t.created
                      FROM tasks t
                    UNION
                    SELECT c.task,
                           c.created
                      FROM contents c
               ) AS stuff
                ORDER BY stuff.created DESC
                LIMIT 1;
                """)
    f = cur.fetchone()
    assert f["id"] is not None
    assert f["id"] > 0

    return f["id"]

downgrade_paths = {
    "doing": "backburner",
    "backburner": "limbo",
}

upgrade_paths = {
    "not doing": "doing",
    "backburner": "doing",
    "limbo": "backburner"
}

# path_migration_comparators = {
#     ("not doing", "doing"): posts(3),
#     ("not doing", "backburner"): interval_("one week"),
#     ("doing", "backburner"): interval_("three days"),
#     ("backburner", "limbo"): interval_("two weeks"),
#     ("blocked", "doing"): posts(1),
# }

dbconn = {
    "host": "localhost",
    "user": "aurynn",
    "password": "aurynn",
    "database": "mangle",
}

def did_add(result):
    #if not args.command:
    #    raise Exception("Syntax error: Requires did context")

    # Must be either 2 or 4 long.
    #assert len(args.command) in [2, 4]

    db = psycopg2.connect(**dbconn)

    desc = result["args"]["description"]
    task = None
    num = None
    try:
        num = int( result["subcmds"]["for"]["task"] )
    except ( TypeError,KeyError ):
        task = last_modified_task(db)
        #num = 1 # This is the oldest task

    section = sections[0]
    try:
        section = result["subcmds"]["in"]["section"]
    except:
        pass


    #settings = dict( map(None, *([iter(args.command)] * 2)) )
    

    cur = db.cursor()
    if task:
        cur.execute("""INSERT INTO contents (description, task) VALUES (%s, %s)""", [ desc, task ])
    else:
        cur.execute("""INSERT INTO contents (description, task) VALUES (%s, 
                           ( SELECT id FROM (
                                SELECT t.id,
                                       row_number() OVER (ORDER BY t.created DESC NULLS LAST) AS rownum
                                  FROM tasks t, 
                                       sections sec
                                 WHERE t.section = sec.name
                                   AND sec.name = %s
                                   ORDER BY t.created DESC
                               ) as sq
                             WHERE rownum = %s ));""", [ 
                       desc, 
                       section, 
                       num ]
        )
    db.commit()


def did_q(result):
    """Gets all the stuff I did for a given thing"""
    db = psycopg2.connect(**dbconn)
    
    num = 1
    try:
        num = int(result["subcmds"]["for"]["task"])
    except TypeError:
        pass
    except KeyError:
        pass

    section = "doing"
    try:
        section = result["subcmds"]["in"]["section"]
    except TypeError:
        pass
    except KeyError:
        pass

    print "section: %s" % section
    cur = db.cursor(cursor_factory=DictCursor)
    cur.execute("""
                SELECT description,
                       created
                  FROM contents c,
                       (SELECT row_number() OVER (order by created desc) as row_number,
                               id
                          FROM tasks t
                         WHERE section = %s
                       ) as tasks
                 WHERE c.task = tasks.id
                   and tasks.row_number = %s
                ORDER BY created DESC
                LIMIT 8
                """, [section, num])
    rows = cur.fetchmany(8) # Get up to 4 rows
    for row in rows:
        print "%s:\t%s" % (row["created"], row["description"] )


def new(results):
    """docstring for new"""

    desc = results["args"]["description"] 
    in_ = sections[0]
    try:
        #print results["subcmds"]
        in_ = results.get("subcmds")["in"]["section"]
    except ( TypeError, KeyError ):
        in_ = sections[0]

    assert in_ in sections
    
    db = psycopg2.connect(**dbconn)
    cur = db.cursor()
    cur.execute("""INSERT INTO tasks (description, section) VALUES (%s, %s)""", [ desc, in_ ])
    db.commit()

        
def doing_q(result):
    """docstring for doing_q"""
    
    s_section = None
    try:
        s_section = result[ "subcmds" ]["in"]["section"]
    except:
        pass

    db = psycopg2.connect(**dbconn)
    cur = db.cursor(cursor_factory=DictCursor)
    cur.execute("""SELECT row_number() OVER (order by created desc) as row_number, 
                          description, 
                          created 
                     FROM tasks 
                    WHERE section = %s 
                      AND done IS NULL
                 ORDER BY created DESC limit 4""", 
                [ s_section or sections[0] ])
    
    rows = cur.fetchmany(4) # Get up to 4 rows
    for row in rows:
        print "%s: %s\t%s" % (row["row_number"], row["created"], row["description"] )


def finished(dct):
    """
    Finished a given task.
    """
    
    try:
        section = dct["subcmds"]["in"]["section"]
    except:
        section = sections[0]
    
    db = psycopg2.connect(**dbconn)
    cur = db.cursor()
    cur.execute("""UPDATE tasks SET done = now() WHERE id = (
        SELECT id FROM(  
            SELECT id, row_number() OVER (order by created desc) as rownum
              FROM tasks
             WHERE section = %s
               AND done is null
            order by created desc
    ) as s
    WHERE rownum = %s);""", [section, dct["args"]["task"] ])

    db.commit()


def done_q(_):
    """docstring for done_q"""
    db = psycopg2.connect(**dbconn)
    cur = db.cursor(cursor_factory=DictCursor)
    cur.execute("""SELECT section, description FROM tasks WHERE done > now() - '1 week'::interval """)
    for row in cur.fetchall():
        print "in %s, %s" % (section, description)


class cmdparser(object):
    def __init__(self, usage=""):
        """docstring for __init__"""
        self.__cmds = {}

    def alias(self, cmd, alias):
        """
        Aliases alias to cmd
        """
        self.__cmds[alias] = self.__cmds[cmd]

    def add_cmd(self, cmd, *args, **kwargs):
        """
        Adds a thing we care about. I guess.
        """
        cmdname = cmd # pull one off the left
        remains = args
        
        if cmdname in self.__cmds:
            raise Exception("cmd '%s' already defined!" % cmdname)
        self.__cmds[cmdname] = {
            "length": len(remains),
            "args": remains,
            "parser": cmdparser(),
            "callable": kwargs.get("func", None)
        }
        # This can, but does not have to be, used.
        return self.__cmds[cmdname]["parser"]
        
    def parse(self, array):
        """
        Parses the input string thing.
        """
        cmdname = array[0] # always the first element
        if cmdname not in self.__cmds:
            raise AttributeError("Command '%s' not defined" % cmdname)
        # DCT is the current command's scope, cmdname
        dct = self.__cmds[cmdname]
        args = array[1: 1 + dct["length"] ]
        
        # What's left after we remove the arguments from the thing.
        remains = array[ 1+dct["length"]:]
        
        subcmd_res = []
        try:
            while remains:
                # Use the subparser to parse the remains
                subcmds = dct["parser"].parse( remains )
                subcmd_res.append( subcmds )
                remains = subcmds["remains"]

        except IndexError:
            subcmds = None
        except AttributeError:
            # The subparser didn't have this command.
            # We should return what we have, and carry on.
            subcmds = None
        return {"cmd": cmdname,
                "args": dict([(argname, argval) for argname, argval in zip(dct["args"], args)]),
                "subcmds": dict( [ (sc["cmd"], sc["args"])  for sc in subcmd_res  ]   ),
                "func": dct["callable"],
                "remains": remains}
        
    def set_callable(self, cmd, func):
        
        try:
            self.__cmds[cmd]["callable"] = func
        except KeyError:
            raise AttributeError("No command %s" % cmd)



def migrator():

    """
    Once per run, handle the queries where we move things around in the 
    upgrade/downgrade system, performing the happy automatic maintenance that
    makes Mangle a useful tool.
    """
    pass



if __name__ == '__main__':
    import argparse

    c = cmdparser(usage="PARSE SOME COMMANDS YO")
    p = c.add_cmd("doing?")
    p.add_cmd("in", "section")

    p = c.add_cmd("doing", "description")
    p.add_cmd("in","section")


    p = c.add_cmd("finished", "task")
    #p.add_cmd("which", )
    p.add_cmd("in", "section")

    p = c.add_cmd("done?")


    p = c.add_cmd("did", "description")
    p.add_cmd("for", "task")
    p.add_cmd("in", "section")


    p = c.add_cmd("did?")
    p.add_cmd("for", "task")
    p.add_cmd("in", "section")

    c.set_callable("doing?",    doing_q)
    c.alias("doing?", "?")
    c.set_callable("doing",       new)
    c.set_callable("finished",  finished)
    c.set_callable("done?",     done_q)
    c.set_callable("did",       did_add)
    c.alias("did", "+")
    c.set_callable("did?",      did_q )

    #c.set_callable("mv",        move)

    # TODO: 
        # A 'move' or 'mv' command
        # make the 'did' output show the associated task
        # Better command parser
        # Better subcommand/extension handling.
          # Should always be an dict?
        # Automate things being moved around the tree based on what I'm doing
        # Automate things being moved around the list based on frequency of updates
        # Move doing/did into an object setup?
        # "Did" should automatically map against the most-recently-edited thing
        # a new 'doing' should automatically mount into the doing category
        # a new category should become the most-recently-edited thing
          # Moving to a new thing should be a conscious choice

    result = c.parse(sys.argv[1:])
    result["func"](result)

    # thing

    migrator()

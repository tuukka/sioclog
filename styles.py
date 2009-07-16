#!/usr/bin/env python

"""styles.py - a module for rendering css stylesheets

Example usage:
from styles import css_stylesheet
css_stylesheet()
"""

def css_stylesheet():
    print """

body {
    margin: 1em;
}

.right-bar {
    float:right;
    margin: 0 0 0.5em 0.5em;
    padding: 0;
}

.format-bar {
    border-style: solid;
    border-color: #9999CC;
    border-width: 2px;
    padding: 0em;
//    float: right;
    margin: 0 0 1.5em 0;
}

.format-bar h3 {
    margin: 0;
    padding: 0.1em 0.5em 0.1em 0.2em;
    background: #ccccff;
}

.format-bar ul, .format-bar li {
    margin: 0;
    padding: 0;
    list-style: none;
}

.format-bar ul {
    padding: 0.1em 0.1em 0.1em 0.2em;
}

.crumb-bar {
    border-style: solid;
    border-color: #9999CC;
    border-width: 2px;
}

.crumb-bar {
    padding: 0.5em;
    margin-bottom: 1.5em;
}

.crumb-bar ul, .crumb-bar li {
    display: inline;
    margin: 0;
    padding: 0;
}

.crumb-bar li:before {
    content: " > ";
//    color: blue;
}

.crumb-bar li:first-child:before {
    content: none;
//    color: blue;
}

.crumb-bar a {
//    color: black;
}

.logo-bar {
//    float: right;
    text-align: center;

//    background: #CCCCFF;

    border-style: solid;
    border-color: #9999CC;
    border-width: 2px;
}

.logo-bar h3 {
    text-align: left;
    margin: 0;
    padding: 0.1em 0.5em 0.1em 0.2em;
    background: #ccccff;
}

th {
    text-align: left;
}

th, td { 
    vertical-align: top;
}

td > a:target {
    background-color: lightblue;
}

img {
    border: none;
    margin: 1em;
}

"""

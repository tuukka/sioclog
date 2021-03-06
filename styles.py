#!/usr/bin/env python

"""styles.py - a module for rendering the CSS stylesheets

Example usage:
from styles import css_stylesheet
css_stylesheet()
"""

def css_stylesheet():
    print """

body {
    margin: 1em;
    background: white;
    color: black;
}

a {
    color: red;
    text-decoration: none;
    border-bottom: 1px solid #ff9999;
}

a:visited {
    color: darkmagenta;
    border-bottom: 1px solid #dd99ff;
}

a:hover, td.time a:hover, td.nick a:hover, a.nick:hover {
    color: red;
    border-bottom: 1px solid red;
//    text-decoration: underline; 
}

a:hover:visited, td.time a:hover:visited, td.nick a:hover:visited, a.nick:hover:visited {
    color: darkmagenta;
    border-bottom: 1px solid darkmagenta;
//    text-decoration: underline; 
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

.crumb-bar ul {
    display: block;
    align: left;
    margin: 0;
    padding: 0;
}

.crumb-bar li {
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

ul.site-bar {
    display: block;
    float: right;
    margin: 0;
    padding: 0;
}

.site-bar li {
    display: inline;
    margin: 0;
    padding: 0;
}

.site-bar li:before {
    content: " | ";
//    color: blue;
}

.site-bar li:first-child:before {
    content: none;
//    color: blue;
}


.logo-bar {
//    float: right;
    text-align: center;

//    background: #CCCCFF;

    border-style: solid;
    border-color: #9999CC;
    border-width: 2px;

    
}

.logo-bar a {
    border: none;
    display: block;
}

.logo-bar img {
    border: none;
    margin: 1em;
}

.logo-bar h3 {
    text-align: left;
    margin: 0;
    padding: 0.1em 0.5em 0.1em 0.2em;
    background: #ccccff;
}

table {
    margin: 1em;
    border-collapse: collapse;
}

table.log {
    background: #f5f5ff;
}

td.time, td.time a {
    color: gray;
    text-decoration: none;
}

td.channel {
    padding-left: 1em;
    padding-right: 0.2em;
}

td.nick {
    text-align: right;
    color: gray;
    padding-left: 1em;
    padding-right: 0.2em;
}

td.nick a, a.nick {
    color: black;
    text-decoration: none;
}

td.content {
    border-left: 1px solid lightgray;
    padding-left: 0.2em;
    white-space: pre-wrap;
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

.logolink {
    white-space: nowrap;
}

.logolink img {
    border: none;
    display: inline;
    margin: 0;
    vertical-align: text-top;
}

"""

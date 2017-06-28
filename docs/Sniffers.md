Sniff Tools
===========
Allows you to apply different filters depending on the server response.
Also, you can support the project and add own filters to repository. Pull requests always open for you.

**NOTICE**: All these filters work with GET request method by default.

Usage
-----

**--sniff file** - Allows you to detect large files from the server response.
*Force scan method:* HEAD
*Positive:* all of sucess pages which contains more than 1mb fall under this filter

```python
opendoor --host www.example.com --sniff file
```

**--sniff indexof** - Allows you to detect empty (Index Of/) Apache directories.
*Force scan method:* GET
*Positive:* all of sucess pages which contains title:(IndexOf|i):title fall under this filter

```python
opendoor --host www.example.com --sniff indexof
```

**--sniff skipempty**  - Allows you to skip blank success pages to select right result
*Force scan method:* GET
*Positive:* all of sucess pages which contains less than 100b are ignored for success

```python
opendoor --host www.example.com --sniff skipempty
```

**--sniff collation**- Heuristic detection of invalid success pages. This is might be when the page has success response but really hasn't meaningful value
*Force scan method:* GET
*Positive:* all successfully loaded pages are compared among themselves, and those that are very similar, fall under this filter and are excluded
*Notice:* The behavior of this filter may vary depending on the source data

```python
opendoor --host www.example.com --sniff collation
```

How this would works?
---------------------
Also you can combine these filters as you prefer.
```python
opendoor --host www.example.com --sniff skipempty,file,collation,indexof --debug 1

[23:16:04] debug:   Starting debug level 1. Using scan method: GET ...
[23:16:04] debug:   Load sniffer: File (detect large files)
[23:16:04] debug:   Load sniffer: IndexOf (detect Index Of/ Apache directories)
[23:16:04] debug:   Load sniffer: Collation (detect and ignore false positive success pages)
[23:16:04] debug:   Load sniffer: SkipEmpty (skip empty success pages)
[23:16:04] info:    Wait, please, checking connect to -> www.example.com:80 ...
[23:16:05] info:    Server www.example.com:80 (93.184.216.34) is online!
[23:16:05] debug:   Read 36312 directories list by line
[23:16:05] debug:   Creating queue with 5 thread(s)...
[23:16:05] info:    Scanning www.example.com ...
```
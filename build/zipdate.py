# Prints the date (YYYY-MM-DD) of a named file inside a zip, e.g. avall.mdb in avall.zip.
import sys,zipfile
z=zipfile.ZipFile(sys.argv[1]); n=sys.argv[2].lower()
i=next(x for x in z.infolist() if x.filename.lower()==n)
print('%04d-%02d-%02d'%i.date_time[:3])

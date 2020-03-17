#!/bin/sh
 
#==============================================
# send Email
#==============================================
sendMail() {
    from="$1"
    to="$2"
    cc="$3"
    bcc="$4"
    subject="$5"
    contents="$6"
 
    inputEncoding="utf-8"
    outputEncoding="iso-2022-jp"
    subjectHead="=?$outputEncoding?B?"
    subjectBody="`echo "$subject" | iconv -f $inputEncoding -t $outputEncoding | base64 | tr -d '\n'`"
    subjectTail="?="
    fullSubject="$subjectHead$subjectBody$subjectTail"
    mailContents="`echo -e $contents | iconv -f $inputEncoding -t $outputEncoding`"
 
    echo "$mailContents" | mail -s "$fullSubject" -c "$cc" -b "$bcc" "$to" -- -f "$from"
    return $?
}
 
from="yuta@isotope2.aori.u-tokyo.ac.jp"
to="yuta@rainbow.iis.u-tokyo.ac.jp"
cc=""
bcc=""
subject=$1
contents=` cat $2 `

sendMail "$from" "$to" "$cc" "$bcc" "$subject" "$contents"
if [ $? -eq 1 ]; then
    echo "send mail failure"
    exit 1
fi
echo "send mail success"

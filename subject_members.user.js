// ==UserScript==
// @name         Bangumi 添加好友也在看
// @namespace    com.everpcpc.bgm
// @version      0.7
// @description  条目页面添加好友在看信息
// @author       everpcpc
// @match        https://bgm.tv/subject/*
// @match        http://bgm.tv/subject/*
// @match        http://bangumi.tv/subject/*
// @match        http://chii.in/subject/*
// @require      https://code.jquery.com/jquery-2.2.4.min.js
// @grant        none
// @encoding     utf-8
// ==/UserScript==

var subject_id = $(location).attr('href').split('/',5)[4];

$('#columnSubjectHomeA').append('<div class="SimpleSidePanel"><h2>哪些好友也在看？</h2><ul id="friend_doings" class="groupsLine"></ul>');

function main() {
    var doings_url = 'https://bgm.everpcpc.com/api/subject/doings/' + subject_id + '/';
    $.get(doings_url, function(data) {
        doings = data.doings;
        var friends_url = $('#badgeUserPanel').children()[6].children[0].href;
        $.get(friends_url, function(data) {
            member_list = $('#memberUserList', $(data)).children();
            for (i = 0; i < member_list.length; i++) {
                members = $(member_list[i]);
                member_url = members.find('a.avatar')[0].href;
                member = member_url.split('/',5)[4];
                if (doings.includes(member)) {
                    $('#friend_doings').append('<a id="'+member+'" href="'+member_url+'"></a>');
                    $('#'+member).append(members.find('.userImage'));
                }
            }
        });
    });
}

// check if it is subject main page
if ($('#subject_detail').length > 0) {
    main();
}


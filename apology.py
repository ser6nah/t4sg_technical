{% extends "layout.html" %}

{% block title %}
    Apology
{% endblock %}

{% block main %}
    <img alt="{{ top }}" class="border" src="http://memegen.link/custom/{{ top | urlencode }}/{{ bottom | urlencode }}.jpg?alt=https://en.meming.world/images/en/7/79/Bernie_Sanders_In_a_Chair_transparent.png" title="{{ top }}">
{% endblock %}

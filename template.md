### 👋 Hello, I'm {{ user.name }}

I joined GitHub on {{ f.date(REGISTRATION_DATE, {dateStyle:"long"}) }}.
I contributed to {{ REPOSITORIES_CONTRIBUTED_TO }} repositories and made {{ COMMITS }} commits.

You can contact me via $\left[\mathbf{matrix}\right]$ at `@allanchain:kde.org`.

I'm a fan of Python and JavaScript/TypeScript! 👇

<%- await embed(`languages`, {languages: true, languages_details: "percentage, bytes-size"}) %>

I'm using {{ plugins.wakatime.editors[0].name }} on {{ plugins.wakatime.os[0].name }}.
A total of {{ f(plugins.wakatime.time.total, {fixed: 1}) }} hours of programming time were recorded last week,
with an average of {{ f(plugins.wakatime.time.daily, {fixed: 1}) }} hours per day. 👇

<%- await embed(`wakatime`, {wakatime: true, wakatime_days: 7, wakatime_limit: 5, wakatime_sections: "languages-graphs"}) %>

By the way, this file was generated with
[lowlighter/metrics@{{ meta.version }}](https://github.com/lowlighter/metrics)
on {{ meta.generated }} (timezone {{ config.timezone.name }}).
Private contributions and achievements are deliberately excluded both in these metrics and in the GitHub contribution graph below.

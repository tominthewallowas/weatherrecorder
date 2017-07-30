SELECT substr(date, 1, 4) as year, count(*) as entries FROM `weather` group by year;

SELECT substr(date, 1, 4) as year, substr(date, 5, 2) as month, count(*) as entries FROM `weather` group by year, month

SELECT substr(date, 1, 4) as year, sum(Precip) as yearly_precip FROM `weather` group by year;

SELECT substr(date, 1, 4) as year, substr(date, 5, 2) as month, sum(Precip) as monthly_precip FROM `weather` group by year, month

SELECT substr(date, 1, 4) as year, substr(date, 5, 2) as month, sum(Precip) as monthly_precip FROM `weather` where substr(date, 1, 4) = 2015 group by year, month

/* Water year Oct through September */
SELECT substr(date, 1, 4) as year, substr(date, 5, 2) as month, sum(Precip) as monthly_precip FROM `weather`
where substr(date, 1, 6) between  201510 and 201609
group by year, month

/* Daily observations */
select DATE_FORMAT(Date, "%m/%d/%Y") as Date, Time, Precip, Comment from weather order by Date desc limit 10

/* Monthly precipitation by the given year */
select substr(Date, 5, 2) as Month, sum(Precip) as Precip from weather where substr(Date, 1, 4) = '%s' group by Month order by Month desc

/* Precipitation for the given year */
select sum(Precip) as Precip from weather where substr(Date, 1, 4) = '%s'" % (date_parms['year']
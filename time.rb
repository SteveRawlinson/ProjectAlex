#!/usr/local/bin/ruby -w

require 'time'
t = nil
while line = gets
  if line =~ /(\d\d:\d\d:\d\d\.\d+:).*is (\w\w)/
    time = $1
    dir = $2

    if t
      last_t = t
      t = Time.parse(time)
      diff = t - last_t
      puts "#{time}  #{dir}  #{t} #{diff}"
    end
    t = Time.parse(time)
  end
end

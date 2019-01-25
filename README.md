# cast2kodi

Simple screencast to kodi tool

Based on my [gist](https://gist.github.com/sphaero/8de9b8fa65d589f50cc7afd315455286) but this time done with Gstreamer to maximize performance and minimize latency.

Technology like this is ubiquitous and completely commodity. However it's %&&$# jungle and the video broadcasting industry is making mess. So this involved some heavy internet-fu to find the right information.

The latency is still way too high however this is caused by Kodi. I haven't found an approach to lowering this in Kodi. If you run this with Gstreamer only the latencies are <1 sec. With UDP even less. However UDP over unreliable networks is just terrible therefore this tool uses TCP.

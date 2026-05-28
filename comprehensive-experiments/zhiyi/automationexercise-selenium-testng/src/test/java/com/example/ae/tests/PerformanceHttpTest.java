package com.example.ae.tests;

import com.example.ae.utils.Config;
import org.testng.Assert;
import org.testng.ITestContext;
import org.testng.annotations.Test;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.*;

/**
 * 性能测试：
 * 使用 Java HttpClient 做轻量并发访问，不启动 100+ 个浏览器。
 * 线程数通过 performance.threads 参数传入，默认 120，满足“并发线程数大于100”的要求。
 */
public class PerformanceHttpTest {

    @Test(description = "性能测试：120线程并发访问首页，统计成功率、平均响应时间、P95")
    public void homePageConcurrentAccess_shouldHaveAcceptableResult(ITestContext context) throws Exception {
        String baseUrl = Config.normalizeBaseUrl(Config.get(context, "baseUrl", "https://automationexercise.com"));
        int threads = Config.getInt(context, "performance.threads", 120);
        int requestsPerThread = Config.getInt(context, "performance.requestsPerThread", 2);

        Assert.assertTrue(threads > 100, "实验要求并发线程数必须大于100");

        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NORMAL)
                .build();

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch start = new CountDownLatch(1);
        List<Long> durations = Collections.synchronizedList(new ArrayList<>());
        List<Integer> statusCodes = Collections.synchronizedList(new ArrayList<>());

        for (int i = 0; i < threads; i++) {
            pool.submit(() -> {
                try {
                    start.await();
                    for (int j = 0; j < requestsPerThread; j++) {
                        long begin = System.nanoTime();
                        try {
                            HttpRequest request = HttpRequest.newBuilder()
                                    .uri(URI.create(baseUrl + "/"))
                                    .timeout(Duration.ofSeconds(20))
                                    .GET()
                                    .header("User-Agent", "Mozilla/5.0 SeleniumLab")
                                    .build();
                            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
                            statusCodes.add(response.statusCode());
                        } catch (Exception e) {
                            statusCodes.add(0);
                        } finally {
                            long end = System.nanoTime();
                            durations.add(TimeUnit.NANOSECONDS.toMillis(end - begin));
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
        }

        long totalBegin = System.currentTimeMillis();
        start.countDown();
        pool.shutdown();
        boolean finished = pool.awaitTermination(5, TimeUnit.MINUTES);
        long totalTime = System.currentTimeMillis() - totalBegin;

        Assert.assertTrue(finished, "性能测试在5分钟内应执行结束");

        int totalRequests = threads * requestsPerThread;
        long success = statusCodes.stream().filter(code -> code >= 200 && code < 400).count();
        double successRate = success * 1.0 / totalRequests;

        List<Long> sorted = new ArrayList<>(durations);
        Collections.sort(sorted);
        double avg = sorted.stream().mapToLong(Long::longValue).average().orElse(0);
        long p95 = sorted.get(Math.max(0, (int) Math.ceil(sorted.size() * 0.95) - 1));
        long max = sorted.get(sorted.size() - 1);

        System.out.println("========== 性能测试结果 ==========");
        System.out.println("URL: " + baseUrl + "/");
        System.out.println("并发线程数: " + threads);
        System.out.println("每线程请求数: " + requestsPerThread);
        System.out.println("总请求数: " + totalRequests);
        System.out.println("成功请求数: " + success);
        System.out.println("成功率: " + String.format("%.2f%%", successRate * 100));
        System.out.println("总耗时: " + totalTime + " ms");
        System.out.println("平均响应时间: " + String.format("%.2f", avg) + " ms");
        System.out.println("P95响应时间: " + p95 + " ms");
        System.out.println("最大响应时间: " + max + " ms");
        System.out.println("HTTP状态码: " + statusCodes);
        System.out.println("================================");

        // 真实公网网站可能出现限流/验证页，阈值不要设置过高。
        Assert.assertTrue(successRate >= 0.70, "成功率不应低于70%，否则说明并发下出现较多失败或被限流");
    }
}

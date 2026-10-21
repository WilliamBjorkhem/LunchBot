package com.example.lunch;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.format.TextStyle;
import java.util.List;
import java.util.Locale;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;
import org.thymeleaf.templateresolver.ClassLoaderTemplateResolver;
import org.thymeleaf.templatemode.TemplateMode;

public class LunchVisualizer {

    public static void main(String[] args) throws IOException {
        if (args.length < 1 || args.length > 2) {
            throw new IllegalArgumentException(
                "Usage: LunchVisualizer <path-to-json-file> [path-to-html-file]");
        }

        List<Restaurant> restaurants = new ObjectMapper()
                .readValue(Path.of(args[0]).toFile(), new TypeReference<List<Restaurant>>() {});

        ClassLoaderTemplateResolver templateResolver = new ClassLoaderTemplateResolver();
        templateResolver.setPrefix("templates/");
        templateResolver.setSuffix(".html");
        templateResolver.setTemplateMode(TemplateMode.HTML);
        templateResolver.setCharacterEncoding(StandardCharsets.UTF_8.name());

        TemplateEngine templateEngine = new TemplateEngine();
        templateEngine.setTemplateResolver(templateResolver);

        Context context = new Context();
        context.setVariable("restaurants", restaurants);
        context.setVariable("weekday", LocalDate.now().getDayOfWeek()
            .getDisplayName(TextStyle.FULL, Locale.ENGLISH));
        String imagePath = "images/lunch-time.png";
        context.setVariable("imagePath", imagePath);

        Path outputPath = Path.of(args.length == 2 ? args[1] : "target/lunch-report.html")
            .toAbsolutePath();
        Path imageOutputPath = outputPath.getParent().resolve(imagePath);
        Files.createDirectories(imageOutputPath.getParent());

        try (InputStream image = LunchVisualizer.class.getResourceAsStream("/templates/lunch-time.png")) {
            if (image == null) {
                throw new IOException("Could not find /templates/lunch-time.png on the classpath");
            }
            Files.copy(image, imageOutputPath, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
        String html = templateEngine.process("lunch-report", context);

        Files.createDirectories(outputPath.getParent());
        Files.writeString(outputPath, html, StandardCharsets.UTF_8);

        System.out.println("HTML report written to " + outputPath);
    }
}

![image](https://github.com/user-attachments/assets/04911a25-54ec-47a1-ad75-688a49f1dc2e)


This is a FOSS Captcha generator designed for websites not using any JavaScript or WebAssembly.
The challenge is simple: name the farthest away shape on the image.

Suggestions are welcome. As of right now this is a very hacky solution.

A simple test page is at your service if you would like to see what the CAPTCHAs look like.

Usage:

    HTTP API:
        Launch the API server (make sur you use your desired port) using:
            freecaptcha.run_api_server(port)
        Requests are formated as follows:
            [JavaScript]
            fetch('/new_captcha?grid_size=8&noise_level=3&return_mode=http');
        And responses as follows:
            [JavaScript]
            {
            "captcha_image": img_base64,
            "answer": solution (a string, such as "square")
            }
    
    Python library:
        Simply import freecaptcha and call the following:
            [Python]
            image, solution = freecaptcha.generate_captcha(grid_size, noise_level, image_generator.RETURN_MODE_RETURN)

This is a FOSS Captcha generator designed for websites not using any JavaScript or WebAssembly.

Suggestions welcome. As of right now this is a very hacky solution.

A simple test page is at your service if you would like to see what the CAPTACHAs look like.

Usage:

    HTTP API:
        Launch the API server (make sur you set the HTTP_PORT to your desired port)
        Requests are formated as follows:
            fetch('/new_captcha?grid_size=8&noise_level=3&return_mode=http');
        And responses as follows:
            {
            "captcha_image": img_base64,
            "answer": solution (a string, such as "square")
            }
    
    Python library:
        Simply import image_generator and call the following:
            image, solution = image_generator.generate_captcha(grid_size, noise_level, image_generator.RETURN_MODE_RETURN)

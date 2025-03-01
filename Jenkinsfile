pipeline{
    agent any
    triggers {
        pollSCM('H/15 * * * *')
    }
    environment {
        IMAGE_NAME = 'os-image-prepper'
    }
    stages{
        stage('Build'){
            steps{
                script{
                    def pushOverviewRepoDir = 'PushDockerHubOverview'
                    if (fileExists(pushOverviewRepoDir)) {
                        sh "echo '\n${pushOverviewRepoDir}/' >> .dockerignore"
                    }
                }
                sh 'docker buildx build --platform linux/amd64,linux/arm64 -t $IMAGE_NAME .'
            }
        }
        stage('Push'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'DockerHubCreds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo "$DOCKER_PASS" | docker login --username "$DOCKER_USER" --password-stdin'
                    sh 'docker tag $IMAGE_NAME "$DOCKER_USER"/$IMAGE_NAME:latest'
                    script{
                        def image_version = sh(
                            script: "grep -oP '(?<=\\*\\*)v[0-9]+\\.[0-9]+(?:\\.[0-9]+)?(?:-[a-z]+)?(?=\\*\\*)' README.md",
                            returnStdout: true
                        ).trim()
                        sh "docker tag $IMAGE_NAME $DOCKER_USER/$IMAGE_NAME:${image_version}"
                    }
                    sh 'docker tag $IMAGE_NAME "$DOCKER_USER"/$IMAGE_NAME:$GIT_COMMIT'
                    sh 'docker push "$DOCKER_USER"/$IMAGE_NAME --all-tags'
                }
            }
        }
        stage('Push Overview'){
            steps{
                script{
                    // Load PushDockerHubOverview on master branch
                    def repoDir = 'PushDockerHubOverview'
                    if (fileExists(repoDir)) {
                        sh "cd ${repoDir} && git pull origin"
                    } else {
                        sh 'git clone https://github.com/Nemesix493/PushDockerHubOverview.git'
                    }
                    def currentBranch = sh(
                        script: "cd ${repoDir} && git rev-parse --abbrev-ref HEAD",
                        returnStdout: true
                    ).trim()
                    if (currentBranch != 'master'){
                        sh "cd ${repoDir} && git checkout master"
                    }

                    // Check if virtual env exist or create it
                    def envDir = repoDir + '/env'
                    if (!fileExists(envDir)) {
                        sh "python3 -m venv ${envDir}"
                    }

                    // Install dependencies
                    sh 'PushDockerHubOverview/env/bin/pip install -r PushDockerHubOverview/requirements.txt'
                }
                withCredentials([usernamePassword(credentialsId: 'DockerHubCreds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]){
                    sh 'cd PushDockerHubOverview/ && env/bin/python -m main -u $DOCKER_USER -r $IMAGE_NAME -t $DOCKER_PASS -f ./../README.md'
                }
            }
        }
    }
}
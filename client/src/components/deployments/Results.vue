<template>
  <iframe ref="frame" :src="url + `/meteor_viewer/`" @load="loadFrame" v-show="loaded" :style="iframe_style" frameborder="0" scrolling="no"></iframe>
</template>

<script>
import axios from 'axios'

export default  {
  data: () => ({
    url: window.location.protocol + '//' + window.location.host,
    loaded: false,
    iframe_src: '',
    iframe_style: 'width:100%; height:'
  }),
  props: {
    src: {
      type: String,
      required: false
    },
    height: {
      type: String,
      required: false
    }
  },
  created() {
    this.parseProps()
  },
  methods: {
    parseProps() {
      this.iframe_src = (this.src === undefined) ? this.$route.params.uri : this.src
      this.iframe_style += (this.height === undefined) ? '100vh' : this.height
    },
    loadFrame() {
      this.getExecution()
    },
    getExecution() {
      // Show Iframe
      this.loaded = true
      // If there's no uri in the url --> do not lookup for an execution
      if (this.iframe_src === undefined) return
      // Add status message
      this.$refs.frame.contentWindow.setLoadingText("- Retrieving Data...")
      // Get Execution Results
      axios.get('/deployments/results', { params: { uri: this.iframe_src } })
        .then((response) => {
          // Inject Execution Data to Iframe
          try {
            this.$refs.frame.contentWindow.initMeteorNext(response.data)
          } catch (error) { 1==1 }
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.$refs.frame.contentWindow.showError(error.response.data.title, error.response.data.description)
        })
    }
  }
}
</script>
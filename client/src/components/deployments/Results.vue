<template>
  <iframe ref="frame" src="http://34.252.139.218:8080/meteor_viewer/" @load="loadFrame" v-show="loaded" :style="iframe_style" frameborder="0" scrolling="no"></iframe>
</template>

<script>
import axios from 'axios'

export default  {
  data: () => ({
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
  computed : {
    //url : function(){ return this.$store.getters.url }
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
      const path = this.$store.getters.url + '/deployments/results'
      axios.get(path, { params: { uri: this.iframe_src } })
        .then((response) => {
          // Inject Execution Data to Iframe
          this.$refs.frame.contentWindow.initMeteorNext(response.data)
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // eslint-disable-next-line
          console.error(error)
        })
    }
  }
}
</script>